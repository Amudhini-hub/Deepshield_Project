from backend.services.authentication import create_access_token, create_refresh_token

print('access1:', create_access_token({'sub': '1'}))
print('access2:', create_access_token({'sub': '1'}))
print('same', create_access_token({'sub': '1'}) == create_access_token({'sub': '1'}))
print('refresh:', create_refresh_token({'sub': '1'}))
