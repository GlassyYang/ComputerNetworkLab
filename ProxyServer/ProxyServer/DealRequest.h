//�������������������֮��Ľ���������������Ӧ����������󲢷�����Ӧ�����ݵĹ��̡�
#ifndef DEALREQUEST
#define DEALREQUEST

#define _REENTRANT
#include <stdio.h>
#include <string.h>
#include <winsock.h>
#include <process.h>
#pragma comment(lib,"ws2_32.lib")

unsigned int WINAPI dealConnect(LPVOID ori);

#define PORT 0X0050		//�˿ں�80�������ֽڱ�ʾ
#define CONNECT_BUFSIZE 4097	//��ƵĴ���������ܹ��������������Ĵ�СΪ4kb��
#define DNS_NORESPONSE_TRY_TIMES	10	//����һ����γ��Եı�������ͨ��gethostbyname���IP��ַʧ�ܵ�ԭ����WSATRY_AGAINʱ���������ԵĴ���
#define HTTP_PORT 80
static const  char *badRequest = "HTTP/1.1 400 Bad Request\r\nConnection: Close\r\n\r\n";
static TIMEVAL waitting_time = { 5l, 0l };		//���ͻ���Ҫ�󱣳�����ʱ������������һ�����󵽴�ǰ�ȴ���ʱ�䡣��ǰ���趨Ϊ5s��
static TIMEVAL timeout = { 2l, 0l };
static const char* unsupported = "HTTP/1.1 501 Not Implemented\r\nConnection: Close\r\n\r\n";
static const char* header_connect = "HTTP/1.1 200 Connection Established\r\n\r\n";
#endif

