import smtpd
import asyncore
import sys

class CustomDebuggingServer(smtpd.DebuggingServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print('\n--- RECEIVED MESSAGE ---')
        print('Peer:', peer)
        print('From:', mailfrom)
        print('To:', rcpttos)
        print('Data:\n', data)
        print('--- END MESSAGE ---\n')
        return

if __name__ == '__main__':
    print('Starting debug SMTP server on localhost:1025')
    server = CustomDebuggingServer(('127.0.0.1', 1025), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        print('SMTP debug server stopped')
        sys.exit(0)
