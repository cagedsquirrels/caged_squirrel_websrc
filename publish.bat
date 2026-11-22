
call build.bat
IF '%ERRORLEVEL%'=='0' GOTO COMMIT
echo An error occurred building the web content. Publish failed!!
exit /b 1

:COMMIT
git add .
git commit -m
IF '%ERRORLEVEL%'=='0' GOTO PUSH
echo An error occurred while adding files to push. Publish failed!!
exit /b 1

:PUSH
git push