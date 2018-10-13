// ProxyServer.cpp : 此文件包含 "main" 函数。程序执行将在此处开始并结束。
//代理服务器的主程序，与用户进行交互并启动代理服务器

#include "MainServer.h"
#include "DealRequest.h"
#include <iostream>
#include <Windows.h>
#include <winsock.h>
#include <process.h>

//程序的主函数，主要是监听用户输入的特定端口，收到连接请求之后就创建子线程处理该请求。
int main()
{
	init();
	int port;
	sockaddr_in caddr;
	printf("Please input a port for this proxy server, between~65535:");
	scanf_s("%d", &port);
	SOCKET server = prepareSock(port);
	if (server == INVALID_SOCKET)
	{
		printf("error on open server, program will exit soon...\n");
		Sleep(1000);
		exit(-1);
	}
	printf("listening port: %d\n", port);
	while (true)
	{
		SOCKET client = accept(server, (sockaddr*)&caddr, NULL);
		if (client == INVALID_SOCKET)
		{
			printf("Error occured while accept. The error code is %d\n", WSAGetLastError());
			exit(-1);
		}
		printf("connection established from %s:%d\n", inet_ntoa(caddr.sin_addr), caddr.sin_port);
		HANDLE handle = (HANDLE)_beginthreadex(NULL, 0,  &dealConnect, (LPVOID)&client, 0, 0);
		CloseHandle(handle);
	}
}
