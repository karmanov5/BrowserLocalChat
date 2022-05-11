import asyncio
import socket
from pywebio.input import *
from pywebio.output import *
from pywebio import start_server, config
from pywebio.session import run_async, defer_call, set_env, info
from user import user

clients = set()
messages = []


@config(theme='dark')
async def main():
    global clients, messages

    set_env(title='Локальный чат на Python', output_animation=False, input_auto_focus=False)

    msg_box = put_scope('messages')
    cl_box = put_scope('clients')
    
    put_grid([
        [put_markdown('**Онлайн**').style('text-align: center; font-style: oblique'), put_markdown('**Сообщения**').style('text-align: center; font-style: oblique')],
        [put_scrollable(cl_box, keep_bottom=True, height=400), put_scrollable(msg_box, keep_bottom=True, height=400)]
    ], cell_widths='150px auto')


    for m in messages[::-1]:
        with use_scope('messages'):
            put_markdown(f'**`{m[0]}`**: {m[1]}' if m[0] != '' else f'📢: {m[1]}', sanitize=True).style('color: #adbfff')
    for u in clients:
        with use_scope('clients'):
            put_scope(u.id, content=put_markdown(f'{u.username}').style('color: #adbfff; text-align: center'))
            

    ip = str(getattr(info, 'user_ip'))
    username = socket.getfqdn(ip)
    if username in [cl.username for cl in clients]:
        username += '_1'
    _user = user(len(clients), ip, username)
    
    clients.add(_user)

    with use_scope('clients'):
        put_scope(_user.id, content=put_markdown(f'{_user.username}').style('color: #94ff8f; text-align: center'))
        
    messages.append(('', f'`{_user.username}` подключился к чату!'))

    # with use_scope('messages'):
    #     put_markdown(f'{_user.username} подключился к чату!')

    @defer_call
    def on_close():
        # with use_scope('messages'):
        #     put_markdown(f'{username} отключился от чата!')
        messages.append(('', f'`{_user.username}` отключился от чата!'))
        clients.remove(_user)
    
    refresh_msgbox_task = run_async(refresh_msgbox(_user))
    refresh_clbox_task = run_async(refresh_clbox())

    while True:
        while True:
            data = await input_group('Введите сообщение', inputs=[
                input(name='msg', placeholder='Введите текст...'),
                actions(name='btns', buttons=['Отправить', 'Многострочный ввод', {'label': 'Выйти из чата', 'type': 'cancel'}])
            ], validate=lambda m: ('msg', 'Поле сообщения не может быть пустым!') if m['btns'] == 'Отправить' and m['msg'] == '' else None)
            if data is None:
                print(f'{_user.username} is disconnected!')
                break
            if data['btns'] == 'Многострочный ввод':
                data = await input_group('Введите сообщение', inputs=[textarea(name='msg', placeholder='Введите текст...'),
                actions(name='btns', buttons=['Отправить', 'Назад', {'label': 'Выйти из чата', 'type': 'cancel'}])
            ], validate=lambda m: ('msg', 'Поле сообщения не может быть пустым!') if m['btns'] == 'Отправить' and m['msg'] == '' else None)
            if data['btns'] == 'Назад':
                pass
            if data['btns'] == 'Отправить':
                break
        messages.append((_user.username, data['msg']))
        if data is None: break
        with use_scope('messages'):
            put_markdown('**`{username}`**: {message}'.format(username=_user.username, message=data['msg']), sanitize=True).style('color: #94ff8f')
    
    refresh_msgbox_task.close()
    refresh_clbox_task.close()
    
    


async def refresh_clbox():
    global clients
    
    cls = clients.copy()

    while True:
        await asyncio.sleep(1)
        if len(clients) > len(cls):
            for cl in clients:
                if cl not in cls:
                    with use_scope('clients'):
                        put_scope(cl.id, content=put_markdown(f'{cl.username}').style('color: #adbfff; text-align: center'))
        
        if len(clients) < len(cls):
            [remove(cl.id) for cl in cls if cl not in clients]
        cls = clients.copy()

    

    
    
async def refresh_msgbox(_user: user):
    global messages

    last_msg_index = len(messages)
    while True:
        await asyncio.sleep(1)
        for m in messages[last_msg_index:]:
            if m[0] != _user.username:
                with use_scope('messages'):
                    put_markdown(f'**`{m[0]}`**: {m[1]}' if m[0] != '' else f'📢: {m[1]}', sanitize=True).style('color: #adbfff')
        last_msg_index = len(messages)






if __name__ == '__main__':
    start_server(main, port=8080, debug=True)

