Bạn là Coding Agent local.

Nhiệm vụ:
Tạo một mini-project Python tên `society_sim`, mô phỏng một xã hội nhỏ kiểu life-simulation game, lấy cảm hứng từ game mô phỏng đời sống nhưng không copy thương hiệu, asset, nhân vật hay nội dung cụ thể nào.

Mục tiêu:
Xây một simulation engine chạy bằng terminal, chưa cần đồ họa. Project phải đủ phức tạp để có:
- nhiều nhân vật
- nhu cầu cơ thể
- cảm xúc
- quan hệ xã hội
- công việc
- tiền
- nhà ở
- lịch ngày/đêm
- hành động tự động
- sự kiện xã hội
- save/load state
- test tự động

Phạm vi bắt buộc:
Chỉ tạo project trong thư mục:

society_sim/

Không sửa orchestrator.
Không sửa MCP.
Không sửa file ngoài `society_sim/` trừ khi cần tạo test runner nhỏ trong `society_sim/`.

Không dùng package ngoài stdlib Python.
Không cài package.
Không commit.

Yêu cầu cấu trúc file:

society_sim/
├── __init__.py
├── models.py
├── rules.py
├── world.py
├── simulation.py
├── persistence.py
├── cli_demo.py
└── test_society_sim.py

Chi tiết chức năng:

1. models.py

Tạo các dataclass:

Person:
- id: str
- name: str
- age: int
- money: float
- traits: list[str]
- skills: dict[str, float]
- needs: dict[str, float]
- mood: str
- home_id: str | None
- job_id: str | None
- relationships: dict[str, float]
- current_action: str

Needs bắt buộc:
- hunger
- energy
- social
- fun
- hygiene

Mỗi need nằm trong khoảng 0.0 đến 100.0.

House:
- id
- name
- capacity
- comfort
- residents: list[str]

Job:
- id
- title
- salary_per_day
- required_skill
- start_hour
- end_hour

WorldEvent:
- tick
- type
- message
- actor_id optional
- target_id optional

WorldState:
- tick
- hour
- day
- people
- houses
- jobs
- events

2. rules.py

Tạo rule functions:

clamp(value, min_value=0.0, max_value=100.0)

decay_needs(person, hour):
- hunger giảm mỗi tick
- energy giảm khi thức
- social giảm nếu không giao tiếp
- fun giảm chậm
- hygiene giảm chậm

calculate_mood(person):
- nếu hunger hoặc energy dưới 20: "distressed"
- nếu social hoặc fun dưới 25: "lonely"
- nếu trung bình needs trên 70: "happy"
- còn lại: "neutral"

choose_action(person, world):
Ưu tiên:
- nếu hunger < 35: "eat"
- nếu energy < 30: "sleep"
- nếu hygiene < 30: "clean"
- nếu đang giờ làm và có job: "work"
- nếu social < 40: "socialize"
- nếu fun < 40: "play"
- còn lại: "idle"

apply_action(person, action, world):
- eat: tăng hunger, giảm money một ít
- sleep: tăng energy, giảm social một ít
- clean: tăng hygiene
- work: tăng money, giảm energy/fun/hygiene, tăng skill liên quan
- socialize: chọn người khác, tăng relationship hai chiều, tăng social
- play: tăng fun, giảm energy
- idle: tăng nhẹ energy hoặc không đổi

3. world.py

Tạo hàm:

create_default_world() -> WorldState

Thế giới mặc định có:
- ít nhất 6 người
- ít nhất 2 nhà
- ít nhất 3 job
- phân người vào nhà
- phân một số người vào job
- tạo relationship ban đầu giữa mọi người là 0 hoặc nhỏ

Tạo hàm:
get_person(world, person_id)
get_job(world, job_id)
get_house(world, house_id)
add_event(world, type, message, actor_id=None, target_id=None)

4. simulation.py

Tạo class Simulation:

__init__(world)
step()
run(ticks)
summary()

Mỗi step:
- tăng tick
- update hour/day
- với mỗi person:
  - decay needs
  - choose action
  - apply action
  - update mood
  - lưu event ngắn
- mỗi ngày mới tạo summary event

summary() trả dict gồm:
- day
- hour
- population
- average_money
- average_needs
- mood_counts
- recent_events

5. persistence.py

Tạo:
save_world(world, path)
load_world(path)

Dùng json stdlib.
Đảm bảo dataclass serialize/deserialize được.

6. cli_demo.py

Khi chạy:

python society_sim/cli_demo.py

Nó phải:
- tạo world mặc định
- chạy simulation 48 ticks
- in summary sau mỗi 6 ticks
- save file society_sim/savegame.json
- load lại file
- in summary sau load

7. test_society_sim.py

Không dùng pytest.
Tạo test bằng assert thường.

Test bắt buộc:
- create_default_world có ít nhất 6 people
- needs luôn nằm trong 0..100 sau 50 ticks
- money thay đổi khi có người đi làm
- relationships tăng sau socialize
- save/load giữ population
- cli_demo logic cơ bản chạy được
- Simulation.run(10) không crash
- summary có đủ key

Khi chạy:

python society_sim/test_society_sim.py

Nếu pass, phải in:

SOCIETY_SIM_TESTS_OK

Quy trình làm việc bắt buộc:

1. Dùng filesystem.create_directory tạo `society_sim`.
2. Tạo từng file bằng file_editor.file_editor_write_lines. Mỗi phần tử trong `lines` là đúng một dòng vật lý của file; mỗi phần tử phải là JSON string dùng dấu nháy kép bên ngoài. Bên trong code Python, ưu tiên dùng nháy đơn để tránh phải escape JSON. Không nhét cả file vào một string dài có `\n`.
3. Sau khi tạo xong, chạy python.run_python với path "society_sim/test_society_sim.py".
4. Nếu test lỗi, đọc stdout/stderr, sửa đúng file liên quan, chạy lại.
5. Sau khi test pass, chạy python.run_python với path "society_sim/cli_demo.py".
6. Final bằng tiếng Việt, báo:
   - file đã tạo
   - tính năng đã có
   - test đã chạy
   - stdout test
   - demo có chạy được không
   - giới hạn hiện tại của project
   - bước phát triển tiếp theo nếu muốn lên bản phức tạp hơn

Luật:
- Không tạo đồ họa.
- Không dùng pygame.
- Không dùng package ngoài.
- Không sửa file ngoài society_sim/.
- Không commit.
- Không bịa test pass nếu chưa thấy SOCIETY_SIM_TESTS_OK.
- Nếu gặp lỗi, phải sửa và chạy lại.
- Chỉ trả JSON tool call hoặc JSON final.python main.py prompts/mega_lifesim_project.md
