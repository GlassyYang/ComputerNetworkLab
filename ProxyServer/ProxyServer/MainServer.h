/*

�ļ��������ڴ�������������̵߳Ĳ���������������������socket�������ض��˿ڵȲ���

*/
#pragma once
#ifndef MAINSERVER
#define MAINSERVER

//ͷ�ļ�������
#include <winsock.h>
#include <stdio.h>

//��������������
#define MAXCONNECT 10	//����listen�������������

//����socket��dll�ļ�
bool init();

//ͨ�����ݵĶ˿ڲͲ�������������һ��socket������ڴ��������з����˴���
//����INVALID_SOCKET
SOCKET prepareSock(u_short port);

#endif // !MAINSERVER

