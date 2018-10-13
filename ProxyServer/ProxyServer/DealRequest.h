//定义代理服务器和浏览器之间的交互，即服务器响应浏览器的请求并返回相应的内容的过程。
#ifndef DEALREQUEST
#define DEALREQUEST

#define _REENTRANT
#include <stdio.h>
#include <string.h>
#include <winsock.h>
#include <process.h>
#pragma comment(lib,"ws2_32.lib")

unsigned int WINAPI dealConnect(LPVOID ori);

#define PORT 0X0050		//端口号80的网络字节表示
#define CONNECT_BUFSIZE 4097	//设计的代理服务器能够接收浏览器请求的大小为4kb。
#define DNS_NORESPONSE_TRY_TIMES	10	//定义一个多次尝试的变量，当通过gethostbyname获得IP地址失败的原因是WSATRY_AGAIN时，继续尝试的次数
#define HTTP_PORT 80
static const  char *badRequest = "HTTP/1.1 400 Bad Request\r\nConnection: Close\r\n\r\n";
static TIMEVAL waitting_time = { 5l, 0l };		//当客户端要求保持连接时，服务器在下一次请求到达前等待的时间。当前的设定为5s。
static TIMEVAL timeout = { 2l, 0l };
static const char* unsupported = "HTTP/1.1 501 Not Implemented\r\nConnection: Close\r\n\r\n";
static const char* header_connect = "HTTP/1.1 200 Connection Established\r\n\r\n";
#endif

