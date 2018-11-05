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
//定义的数据结构
typedef struct tree_node{
	u_int nexthop;	//表示下一跳的端口号,当没有下一跳的时候,默认值为0xffffffff.
	struct tree_node *Lchild;	//表示树的左子节点
	struct tree_node *Rchild;	//表示树的右子节点
} tree_node;
//定义用于树操作的宏和函数
#define NEWNODE (tree_node*)malloc(sizeof(tree_node))

void initNode(tree_node *node)
{
	node->nexthop = 0xffffffff;
	node->Lchild = NULL;
	node->Rchild = NULL;
	return;
}

tree_node *root;	//树的根

void stud_Route_Init()
{
	root = NEWNODE;
	initNode(root);
	return;
}

void stud_route_add(stud_route_msg *proute)
{
	u_int masklen = proute->masklen >> 24, mask = 0xffffffff << 32 - masklen, route = proute->dest;
	//提取route
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
	//提取数据包中的ip地址
	for(int i = 16; i < 20; i++)
	{
		pkg_addr += (u_char)pBuffer[i];
		if(i != 19)
		{
			pkg_addr <<= 8;
		}
	}
	//如果ip地址等于本地的ip地址，向上层交付该ip数据包
	if(pkg_addr == getIpv4Address())
	{
		fwd_LocalRcv(pBuffer, length);
		return 0;
	}
	tree_node *cur = root, *temp = root;
	u_int hop = 0xffffffff;
	//在树上循环查找下一跳，因为树的高度最高只有33，所以只需循环33次
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
				//找到了该数据包的目的端口，进行转发;
				//更新该数据包的TTL，如果更新后的值为0则丢弃该数据包。
				pBuffer[8] -= 1;
				if(pBuffer[8] == 0)
				{
					fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
					return 1;
				}
				//更新数据包的校验和
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
				//发送数据包
				fwd_SendtoLower(pBuffer, length, temp->nexthop);
				return 0;
			}
			else if(hop != -1)
			{
				//将该数据包转发到之前记录到的端口上
				pBuffer[8] -= 1;
				if(pBuffer[8] == 0)
				{
					fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
					return 1;
				}
				//更新数据包的校验和
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
				//发送数据包
				fwd_SendtoLower(pBuffer, length, hop);
				return 0;
			}
			else
			{
				//如果先前没有记录，则说明在该数据包的查找地址上没有找到能够转发该数据包的端口，说明没有该路由
				fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
				return 1;
			}
		}else if(cur->nexthop != 0xffffffff)
		{
			//记录当前的端口以便后面使用到的时候进行端口的转发。
			hop = cur->nexthop;
		}
		pkg_addr <<= 1;
	}
	fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
	return 1;
}

