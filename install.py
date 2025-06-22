api_id = input('API_ID: ')
api_hash = input('API_HASH: ')

bot_token = input('BOT_TOKEN: ')

f = open('.env', 'w')
f.write(f'API_ID={api_id}\n')
f.write(f'API_HASH={api_hash}\n')
f.write(f'BOT_TOKEN={bot_token}\n')
f.close()

print("Successful")
