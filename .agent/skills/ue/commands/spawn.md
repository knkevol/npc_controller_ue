---
description: UE5 물리 액터 스폰
allowed-tools: Bash(curl:*)
argument-hint: <name> [mesh] [location] [options...]
---

물리 액터를 스폰해라. HTTP 서버에 Python 스크립트를 전송한다.

## 사용 가능한 함수

- `skills.physics_actor.spawn_physics_blueprint_actor(name, mesh_path, location, scale, color, simulate_physics, gravity_enabled, mass)`
- `skills.structures.spawn_static_mesh_actor(name, location, scale, mesh_path, rotation)`
- `skills.structures.batch_spawn(specs, mesh_path)`

## 호출 방법

```bash
curl -s -X POST http://127.0.0.1:8080/execute -H "Content-Type: application/json" -d "{\"mode\":\"editor\",\"script\":\"from skills.physics_actor import spawn_physics_blueprint_actor\\nresult.update(spawn_physics_blueprint_actor(params['name'], location=params.get('location', [0,0,0])))\",\"params\":{\"name\":\"MyCube\",\"location\":[0,0,100]}}"
```

사용자 요청: $ARGUMENTS
