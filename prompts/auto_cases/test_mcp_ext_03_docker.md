Test Docker MCP an toan.

Yeu cau:
1. Goi docker.docker_ps voi all true timeout 20.
2. Goi docker.docker_compose_ps voi timeout 20.
3. Goi docker.docker_compose_logs voi service "qdrant" tail 30 timeout 30.
4. Khong goi up/stop/delete/prune.
5. Final bang tieng Viet, bat buoc co DOCKER_MCP_OK va bao cao:
   - docker ps ok hay dependency/environment failure
   - moi docker result co command_metadata.security_risk khong
   - compose ps/logs doc duoc khong
   - xac nhan khong dung destructive Docker command

Khong sua file. Khong commit.
Chi tra JSON tool call hoac JSON final.
