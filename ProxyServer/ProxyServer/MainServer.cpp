#include  "MainServer.h"

bool init()
{
	WORD version = MAKEWORD(2, 1);
	WSADATA wsaData;
	int err = WSAStartup(version, &wsaData);
	if (err != 0)
	{
		printf("cannot load winsock dynamic link lib!\n");
		return false;
	}
	else
	{
		printf("information on socket used:\n");
		printf("winsock version will be used: %u.%u\n", LOBYTE(wsaData.wVersion), HIBYTE(wsaData.wVersion));
		printf("newest winsock version this dll supported: %u.%u\n", LOBYTE(wsaData.wHighVersion), HIBYTE(wsaData.wHighVersion));
		printf("System info:%s\n", wsaData.szSystemStatus);
	}
	return true;
}

SOCKET prepareSock(u_short port)
{
	//int err;
	SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
	if (INVALID_SOCKET == sock)
	{
		printf("create socket failed. the error code is %d\n", WSAGetLastError());
		return INVALID_SOCKET;
	}
	sockaddr_in addr;
	addr.sin_family = AF_INET;
	addr.sin_addr.S_un.S_addr = INADDR_ANY;
	addr.sin_port = htons(port);
	if (bind(sock, (SOCKADDR*)&addr, sizeof(SOCKADDR)) == SOCKET_ERROR)
	{
		printf("Bind failed!\n");
		return INVALID_SOCKET;
	}
	if (listen(sock, MAXCONNECT) == SOCKET_ERROR)
	{
		printf("Trying on lintening failed!. the error code is %d\n", WSAGetLastError());
		return INVALID_SOCKET;
	}
	return sock;
}


