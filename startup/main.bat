call cd "C:\Program Files\OpenVPN\config"
call "C:\Program Files\OpenVPN\bin\openvpn-gui.exe" --connect vpn-diego.ovpn
call cd "C:\Users\GIAFyS\Downloads\tfg"
call venv\Scripts\activate
call timeout 60
call START /B ssh -f -ND 8443 root@10.243.64.4
call cd "C:\Users\GIAFyS\Downloads\tfg\watchdog"
call START /B python slave.py
call START /B python main.py
