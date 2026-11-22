python -m pip install -r requirements.txt
IF '%ERRORLEVEL%'=='0' GOTO build
echo An error installing python modules. Build failed!!
exit /b 1

:BUILD
python build.py --sync ..\coffee
IF '%ERRORLEVEL%'=='0' GOTO DONE
echo An error occurred building hte web content. Build failed!!
exit /b 1

:DONE