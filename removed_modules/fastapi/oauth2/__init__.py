#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import timedelta

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from .model import Token
from .util import authenticate_user, create_access_token

ACCESS_TOKEN_EXPIRE_MINUTES = 120


async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_expires = timedelta(seconds=20)
    access_token = create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type='bearer')


# @app.get('/user', response_model=User)
# async def read_users_me(current_user: User = Depends(get_current_user)):
#     return current_user
