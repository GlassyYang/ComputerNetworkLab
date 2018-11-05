/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include "sysInclude.h"

extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

// implemented by students

int stud_ip_recv(char *pBuffer,unsigned short length)
{
	//检查ip地址是不是本机的ip地址，如果不是的话抛弃该分组。
	int pkg_addr = 0;
	for(int i = 0; i < 4; i++)
	{
		pkg_addr += pBuffer[16 + i];
		if( i != 3)
		{
			pkg_addr <<= 8;
		}
	}
	if(pkg_addr != getIpv4Address())
	{
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);
		return 1;
	}
	//检验ip地址的版本号，不是4的话返回1
	int version = pBuffer[0];
	version &= 0x000000f0;
	version >>= 4;
	if(version != 4)
	{
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR);
		return 1;
	}
	//检查数据报的首部长度，应该在20到60之间，超过的话丢弃该分组。
	int headerLength = (pBuffer[0] & 0x0f) << 2;
	if(headerLength < 20 || headerLength > 60)
	{
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR);
		return 1;
	}	
	//检查数据报的TTL，等于0的话抛弃该分组。
	int ttl = pBuffer[8];
	if(ttl == 0)
	{
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR);
		return 1;
	}
	//检查数据包的校验和，如果错误的话抛弃该分组。
	u_int checksum = 0;
	for(int i = 0; i < headerLength; i += 2)
	{
		checksum += (u_char)pBuffer[i] << 8;
		checksum += (u_char)pBuffer[i+1];
		int temp = (checksum & 0x00010000);
		checksum &= 0x0000ffff;
		checksum += temp;
	}
	if(checksum != 0xffff)
	{
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);
		return 1;
	}
	int up_length = *((short*)(pBuffer + 2));
	ip_SendtoUp(pBuffer + headerLength, up_length - headerLength);
	return 0;
}
//需要实现IPv4分组的封装发送功能,
int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
	char* pkg = (char*)malloc(len + 20);
	int to_len = len + 20;
	memcpy(pkg + 20, pBuffer, len);
	pkg[0] = 0x45;
	pkg[1] = 0x00;
	pkg[2] = (char)(to_len >> 8);
	pkg[3] = (char)to_len;
	srand(time(NULL));
	short sign = rand();
	pkg[4] = (char)(sign >> 8);
	pkg[5] = (char)sign;
	pkg[6] = 0x60;
	pkg[7] = 0;
	pkg[8]  = ttl;
	pkg[9] = protocol;
	pkg[10] = 0;
	pkg[11] = 0;
	for(int i = 0; i < 4; i++)
	{
		pkg[15 - i] = (char)(srcAddr & 0xff);
		srcAddr >>= 8;
	}
	for(int i = 0; i < 4; i++)
	{
		pkg[19 - i] = (char)(dstAddr & 0xff);
		dstAddr >>= 8;
	}
	int checksum = 0;
	for(int i = 0; i < 20; i += 2)
	{
		checksum += (u_char)pkg[i] << 8;
		checksum += (u_char)pkg[i + 1];
		int temp = checksum & 0x00010000;
		checksum &= 0x0000ffff;
		checksum += temp >> 16;
	}
	pkg[11] = ~(u_char)(checksum & 0xff);
	checksum >>= 8;
	pkg[10] = ~(u_char)(checksum & 0xff);
	ip_SendtoLower(pkg, to_len);
	return 0;
}
