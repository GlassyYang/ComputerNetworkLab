
#include "DealRequest.h"

//获得和服务器端通信的socket，传入的参数是服务器端的IP地址
SOCKET getSocket(char* host) 
{
	hostent* hostIp = gethostbyname(host);
	//这儿需要处理异常
	if (hostIp == NULL)
	{
		printf("failed whith get IP address by host name\n");
		return INVALID_SOCKET;
	}
	sockaddr_in addr;
	addr.sin_family = hostIp->h_addrtype;
	addr.sin_addr = *((in_addr*)*hostIp->h_addr_list);
	//printf("%s\n", inet_ntoa(addr.sin_addr));
	addr.sin_port = htons(HTTP_PORT);
	SOCKET client = socket(AF_INET, SOCK_STREAM, 0);
	if (client == INVALID_SOCKET) 
	{
		printf("failed on create client socket!");
		exit(1);
	}
	if (connect(client, (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR)
	{
		printf("error on connect to target host!\n");
		//printf("%d", WSAGetLastError());
		exit(2);
	}
	return client;
}

//退出时清理buffer和关闭socket；
void clear(SOCKET sock, char* buf)
{
	if (closesocket(sock) == SOCKET_ERROR)
	{
		printf("Error occured while closing connection.\n");
	}
	if (buf != NULL)
	{
		free(buf);
	}
}

//函数用来确定该代理服务器能够处理的HTTP请求。
//buf为浏览器的HTTP请求，当是POST、GET、HEAD的时候返回true，不是的时候返回false。
bool support(char* buf)
{
	if (strncmp(buf, "GET",3) != 0)
	{
		if (strncmp(buf, "POST", 4) != 0)
		{
			if (strncmp(buf, "HEAD", 4) != 0)
			{
				if (strncmp(buf, "CONNECT", 7) != 0)
				{
					return false;
				}
			}
		}
	}
	return true;
}

//从服务器接收数据，然后将数据返回给浏览器。由于接收的缓存有限（只有4kb），
//所以需要经历从服务器到客户端的多次接收和发送才能完成一次response的传送。
void server2origin(SOCKET server, SOCKET origin)
{
	char *buf = (char*)malloc(CONNECT_BUFSIZE);
	FD_SET set;
	FD_ZERO(&set);
	FD_SET(server, &set);

	if (buf == NULL)
	{
		printf("There are no enough memory!\n");
		exit(3);
	}
	//从服务器接收第一部分，由于缓存大小适当，所以第一次一定能完整的接受完respond头部信息，
	//然后从头部信息获得Content-Lencth的值，然后 通过这个值的大小以及接收到的数据的大小判断
	//是否多次从服务器接收数据，以及从服务器接收多少次数据。
	while (true)
	{
		int temp = select(NULL, &set, NULL, NULL, &timeout);
		if (temp == SOCKET_ERROR)
		{
			printf("A socket error happend while waitting for another request.\n");
			break;
		}
		else if (temp == 0)
		{
			break;
		}
		int recv_size = recv(server, buf, CONNECT_BUFSIZE, 0);
		if (recv_size == SOCKET_ERROR)
		{
			printf("Error occured while receiving data to origin client.\n");
			return;
		}
		else if (recv_size == 0)
		{
			break;
		}
		if (send(origin, buf, recv_size, 0) == SOCKET_ERROR)
		{
			printf("Error occured while sending data to origin client.\n");
			return;
		}
	}
	return;
}

//处理连接，是线程中运行的函数。
unsigned int WINAPI dealConnect(LPVOID ori)
{
	SOCKET origin = *((SOCKET*)ori);
	char* buf = (char*)malloc(CONNECT_BUFSIZE);
	int size_recv = -1;
	if (buf == NULL)
	{
		printf("Error! no enough memory!\n");
		clear(origin, NULL);
		return 0;
	}
	while (true)
	{
		bool close = false;
		size_recv = recv(origin, buf, CONNECT_BUFSIZE - 1, 0);
		if (size_recv == SOCKET_ERROR)
		{
			printf("error on recving data from browser, connection will closed.\n");
			clear(origin, buf);
			break;
		}
		else if (size_recv == 0)
		{
			printf("Receive nothing from browser,connection will be closed.\n");
			clear(origin, buf);
			break;
		}
		buf[size_recv] = '\0';
		//printf_s(buf);
		if (support(buf))
		{
			//查找浏览器定义的连接状态
			char *index_c = strstr(buf, "Connection:");		//找到Connection头的位置

			//如果浏览器的request头中不含有Connection字段，那么就检查HTTP的协议版本，
			//根据HTTP的协议版本确定连接的默认操作。
			if (index_c == NULL)
			{
				if (strstr(buf, "HTTP/1.0"))
				{
					close = true;
				}
				else
				{
					close = false;
				}
			}
			else
			{
				index_c += 11;
				if (*index_c == ' ')
				{
					index_c++;
				}
				if (strncmp(index_c, "close", 5) == 0)
				{
					close = true;
				}
				else
				{
					close = false;
				}
			}
			if (strncmp(buf, "CONNECT", 7) == 0)
			{
				if (send(origin, unsupported, sizeof(unsupported), 0) == SOCKET_ERROR)
				{
					printf("Error while sending data to browser.\n");
					clear(origin, buf);
					break;
				}
				printf("Connect method received from browser.\n");
				if (close)
				{
					clear(origin, buf);
					break;
				}
				else
				{
					continue;
				}
			}

			//查找目的主机的主机名和浏览器定义的连接状态
			char*index_h = strstr(buf, "Host:");	//找到Host头的位置
			if (index_h == NULL)
			{
				if (send(origin, badRequest, sizeof(badRequest), 0) == SOCKET_ERROR)
				{
					printf("Error while sending data to browser\n");
					clear(origin, buf);
					break;
				}
			}
			index_h += 5;
			if (*index_h == ' ')
			{
				index_h++;
			}
			int len = 0;
			//通过查找到的主机名创建到主机的连接
			for (; *(index_h + len) != '\r'; len++);
			*(index_h + len) = '\0';
			SOCKET server = getSocket(index_h);
			//获取到INVALID_SOCKET的原因是客户端发送的request中host头不正确；
			if (server == INVALID_SOCKET)
			{
				if (send(origin, badRequest, sizeof(badRequest), 0) == SOCKET_ERROR)
				{
					printf("Error on sending badRequest data to browser!\n");
					break;
				}
			}
			*(index_h + len) = '\r';

			if (send(server, buf, size_recv, 0) == SOCKET_ERROR)
			{
				printf("Error on sending request to server!\n");
				break;
			}
			//将从服务器接收到的respond数据发送给浏览器
			server2origin(server, origin);
			//如果客户端发送的request头部要求关闭连接的话，就关闭连接并退出。
			if (close)
			{
				clear(origin, buf);
				clear(server, NULL);
				break;
			}
			//如果客户端要求保持连接的打开，则服务器等待一个时间，在等待时间过去之后如果客户端没有发送请求，则主动关闭连接。

			//使用select函数监听origin套接字
			FD_SET set;
			FD_ZERO(&set);
			FD_SET(origin, &set);

			int temp = select(NULL, &set, NULL, NULL, &waitting_time);
			if (temp == SOCKET_ERROR)
			{
				printf("A socket error happend while waitting for another request.\n");
				clear(origin, buf);
				clear(server, NULL);
				break;
			}
			else if (temp == 0)
			{
				clear(origin, buf);
				clear(server, NULL);
				break;
			}
		}
		else
		{
			printf("Unsupport method detected.\n");
			if (send(origin, unsupported, sizeof(unsupported), 0) == SOCKET_ERROR)
			{
				printf("Error while sending data to browser.\n");
			}
			clear(origin, buf);
			break;
		}
	}
	_endthreadex(0);
	return 0;
}