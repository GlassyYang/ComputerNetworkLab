def checksum(data):
    if len(data) % 2:
        data += b'\x00'
    ans = 0
    for i in range(0, len(data), 2):
        temp = int.from_bytes(data[i:i+2], byteorder='big')
        ans += temp
        temp = ans >> 16
        if temp != 0:
            ans += temp
            ans = ans ^ 0x10000
    return ans


if __name__ == '__main__':
    ans = checksum(b'\xa5\x46\xf4\x23\xf4\x24')
    print(ans)
