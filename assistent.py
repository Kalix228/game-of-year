import time
while 1:
    with open('main.py', 'r', encoding='utf-8') as f:
        f1 = f.read()
    with open('main_client.py', 'r', encoding='utf-8') as f:
        f2 = f.read()

    if not f1.replace('self.host = True', '') == f2.replace('self.host = False', ''):
        f2 = f1.replace('self.host = True', 'self.host = False')
        with open('main_client.py', 'w', encoding='utf-8') as f:
            f.write(f2)
        print('writed')
    else:
        print('not writed')
    time.sleep(5)