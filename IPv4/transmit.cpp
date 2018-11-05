/*
* THIS FILE IS FOR IP FORWARD TEST
*/
#include "sysInclude.h"

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students
//��������ݽṹ
typedef struct tree_node{
	u_int nexthop;	//��ʾ��һ���Ķ˿ں�,��û����һ����ʱ��,Ĭ��ֵΪ0xffffffff.
	struct tree_node *Lchild;	//��ʾ�������ӽڵ�
	struct tree_node *Rchild;	//��ʾ�������ӽڵ�
} tree_node;
//���������������ĺ�ͺ���
#define NEWNODE (tree_node*)malloc(sizeof(tree_node))

void initNode(tree_node *node)
{
	node->nexthop = 0xffffffff;
	node->Lchild = NULL;
	node->Rchild = NULL;
	return;
}

tree_node *root;	//���ĸ�

void stud_Route_Init()
{
	root = NEWNODE;
	initNode(root);
	return;
}

void stud_route_add(stud_route_msg *proute)
{
	u_int masklen = proute->masklen >> 24, mask = 0xffffffff << 32 - masklen, route = proute->dest;
	//��ȡroute
	int temp = 0;
	for(int i = 0; i < 4; i++)
	{
		temp <<= 8;
		temp += (route & 0xff);
		route >>= 8;
	}
	route = temp & mask;
	int num = 0;
	tree_node *cur = root;
	int i = 0;
	while(mask != 0)
	{
		i++;
		num = route & 0x80000000;
		if(num == 0)
		{
			if(cur->Lchild == NULL)
			{
				cur->Lchild = NEWNODE;
				initNode(cur->Lchild);
			}
			cur = cur->Lchild;
		}
		else
		{
			if(cur->Rchild == NULL)
			{
				cur->Rchild = NEWNODE;
				initNode(cur->Rchild);
			}
			cur = cur->Rchild;
		}
		route <<= 1;
		mask <<= 1;
	}
	cur->nexthop = proute->nexthop;
	return;
}

int stud_fwd_deal(char *pBuffer, int length)
{
	UINT32 pkg_addr = 0;
	//��ȡ���ݰ��е�ip��ַ
	for(int i = 16; i < 20; i++)
	{
		pkg_addr += (u_char)pBuffer[i];
		if(i != 19)
		{
			pkg_addr <<= 8;
		}
	}
	//���ip��ַ���ڱ��ص�ip��ַ�����ϲ㽻����ip���ݰ�
	if(pkg_addr == getIpv4Address())
	{
		fwd_LocalRcv(pBuffer, length);
		return 0;
	}
	tree_node *cur = root, *temp = root;
	u_int hop = 0xffffffff;
	//������ѭ��������һ������Ϊ���ĸ߶����ֻ��33������ֻ��ѭ��33��
	for(int i = 0; i <= 32; i++)
	{
		temp = cur;
		if((pkg_addr & 0x80000000) == 0)
		{
			cur = cur->Lchild;
		}
		else
		{
			cur = cur->Rchild;
		}
		if(cur == NULL)
		{
			if(temp->nexthop != 0xffffffff)
			{
				//�ҵ��˸����ݰ���Ŀ�Ķ˿ڣ�����ת��;
				//���¸����ݰ���TTL��������º��ֵΪ0���������ݰ���
				pBuffer[8] -= 1;
				if(pBuffer[8] == 0)
				{
					fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
					return 1;
				}
				//�������ݰ���У���
				int checksum = 0;
				pBuffer[11] = 0;
				pBuffer[10] = 0;
				for(int i = 0; i < 20; i += 2)
				{
					checksum += (u_char)pBuffer[i] << 8;
					checksum += (u_char)pBuffer[i + 1];
					int temp = checksum & 0x00010000;
					checksum &= 0x0000ffff;
					checksum += temp >> 16;
				}
				pBuffer[11] = ~(u_char)(checksum & 0xff);
				checksum >>= 8;
				pBuffer[10] = ~(u_char)(checksum & 0xff);
				//�������ݰ�
				fwd_SendtoLower(pBuffer, length, temp->nexthop);
				return 0;
			}
			else if(hop != -1)
			{
				//�������ݰ�ת����֮ǰ��¼���Ķ˿���
				pBuffer[8] -= 1;
				if(pBuffer[8] == 0)
				{
					fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
					return 1;
				}
				//�������ݰ���У���
				int checksum = 0;
				pBuffer[11] = 0;
				pBuffer[10] = 0;
				for(int i = 0; i < 20; i += 2)
				{
					checksum += (u_char)pBuffer[i] << 8;
					checksum += (u_char)pBuffer[i + 1];
					int temp = checksum & 0x00010000;
					checksum &= 0x0000ffff;
						checksum += temp >> 16;
				}
				pBuffer[11] = ~(u_char)(checksum & 0xff);
				checksum >>= 8;
				pBuffer[10] = ~(u_char)(checksum & 0xff);
				//�������ݰ�
				fwd_SendtoLower(pBuffer, length, hop);
				return 0;
			}
			else
			{
				//�����ǰû�м�¼����˵���ڸ����ݰ��Ĳ��ҵ�ַ��û���ҵ��ܹ�ת�������ݰ��Ķ˿ڣ�˵��û�и�·��
				fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
				return 1;
			}
		}else if(cur->nexthop != 0xffffffff)
		{
			//��¼��ǰ�Ķ˿��Ա����ʹ�õ���ʱ����ж˿ڵ�ת����
			hop = cur->nexthop;
		}
		pkg_addr <<= 1;
	}
	fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
	return 1;
}

