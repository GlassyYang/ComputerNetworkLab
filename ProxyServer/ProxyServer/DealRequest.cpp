
#include "DealRequest.h"

//��úͷ�������ͨ�ŵ�socket������Ĳ����Ƿ������˵�IP��ַ
SOCKET getSocket(char* host) 
{
	hostent* hostIp = gethostbyname(host);
	//�����Ҫ�����쳣
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

//�˳�ʱ����buffer�͹ر�socket��
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

//��������ȷ���ô���������ܹ������HTTP����
//bufΪ�������HTTP���󣬵���POST��GET��HEAD��ʱ�򷵻�true�����ǵ�ʱ�򷵻�false��
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

//�ӷ������������ݣ�Ȼ�����ݷ��ظ�����������ڽ��յĻ������ޣ�ֻ��4kb����
//������Ҫ�����ӷ��������ͻ��˵Ķ�ν��պͷ��Ͳ������һ��response�Ĵ��͡�
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
	//�ӷ��������յ�һ���֣����ڻ����С�ʵ������Ե�һ��һ���������Ľ�����respondͷ����Ϣ��
	//Ȼ���ͷ����Ϣ���Content-Lencth��ֵ��Ȼ�� ͨ�����ֵ�Ĵ�С�Լ����յ������ݵĴ�С�ж�
	//�Ƿ��δӷ������������ݣ��Լ��ӷ��������ն��ٴ����ݡ�
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

//�������ӣ����߳������еĺ�����
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
			//������������������״̬
			char *index_c = strstr(buf, "Connection:");		//�ҵ�Connectionͷ��λ��

			//����������requestͷ�в�����Connection�ֶΣ���ô�ͼ��HTTP��Э��汾��
			//����HTTP��Э��汾ȷ�����ӵ�Ĭ�ϲ�����
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

			//����Ŀ������������������������������״̬
			char*index_h = strstr(buf, "Host:");	//�ҵ�Hostͷ��λ��
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
			//ͨ�����ҵ�������������������������
			for (; *(index_h + len) != '\r'; len++);
			*(index_h + len) = '\0';
			SOCKET server = getSocket(index_h);
			//��ȡ��INVALID_SOCKET��ԭ���ǿͻ��˷��͵�request��hostͷ����ȷ��
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
			//���ӷ��������յ���respond���ݷ��͸������
			server2origin(server, origin);
			//����ͻ��˷��͵�requestͷ��Ҫ��ر����ӵĻ����͹ر����Ӳ��˳���
			if (close)
			{
				clear(origin, buf);
				clear(server, NULL);
				break;
			}
			//����ͻ���Ҫ�󱣳����ӵĴ򿪣���������ȴ�һ��ʱ�䣬�ڵȴ�ʱ���ȥ֮������ͻ���û�з��������������ر����ӡ�

			//ʹ��select��������origin�׽���
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