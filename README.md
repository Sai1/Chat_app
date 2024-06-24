# Chat_app
Group chat and one to one messaging chat app using TCP sockets

group chat app using tcp sockets

Features

1.login/register available with users saved in DB
2.Displays history of messages saved in DB
4.Implemented multiple chat rooms
6.one-one messaging/private messaging
7.Custom protocol header in application layer level #[IP Header][TCP Header][Custom Header][Message Content], since I used tcp sockets lower layer level headers are controlled by OS and I can customise only application layer header.If I use raw sockets I can control all layer headers(ethernet,ip and tcp)


tested and removed features
1.encrypted socket with TLS/SSL security ( can check in wireshark,which secure communication at the transport layer. They sit between the application layer (which generates the data) and the transport layer (which handles data transmission).)
