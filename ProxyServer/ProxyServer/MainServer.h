/*

文件定义了在代理服务器中主线程的操作函数，包括创建并绑定socket，监听特定端口等操作

*/
#pragma once
#ifndef MAINSERVER
#define MAINSERVER

//头文件声明：
#include <winsock.h>
#include <stdio.h>

//常量定义声明：
#define MAXCONNECT 10	//定义listen是最大连接数量

//加载socket的dll文件
bool init();

//通过传递的端口餐参数创建并返回一个socket，如果在创建过程中发生了错误，
//返回INVALID_SOCKET
SOCKET prepareSock(u_short port);

#endif // !MAINSERVER

