Ban la Coding Agent local.

Nhiem vu:
Tao mot mini-project Python ten `society_sim_complex`, mo phong mot he sinh thai
life-simulation terminal phuc tap hon ban `society_sim`. Lay cam hung tu game
mo phong doi song, nhung khong copy thuong hieu, asset, nhan vat, lore, UI hay
noi dung cu the nao.

Muc tieu:
Xay mot simulation engine chay bang terminal, stdlib-only, co du domain logic de
test nang luc LLM khi phai di tu business logic -> thiet ke -> code -> test.
Project phai co autonomy planner, household economy, relationships, schedules,
events, memory, persistence versioned JSON va test tu dong.

Pham vi bat buoc:
Chi tao va sua file trong thu muc:

society_sim_complex/

Khong sua orchestrator.
Khong sua MCP.
Khong sua file ngoai `society_sim_complex/`.
Khong dung package ngoai stdlib Python.
Khong cai package.
Khong commit.
Khong tao do hoa.
Khong dung pygame.

Yeu cau cau truc file:

society_sim_complex/
|-- __init__.py
|-- constants.py
|-- models.py
|-- catalog.py
|-- rules.py
|-- actions.py
|-- autonomy.py
|-- relationships.py
|-- events.py
|-- economy.py
|-- world.py
|-- simulation.py
|-- persistence.py
|-- reporting.py
|-- cli_demo.py
`-- test_society_sim_complex.py

Tong quan domain:

The gioi mac dinh phai co:
- it nhat 10 people
- it nhat 3 households
- it nhat 4 homes
- it nhat 6 jobs
- it nhat 6 locations
- it nhat 12 action types
- it nhat 6 random/daily event types
- it nhat 8 needs
- it nhat 8 traits
- it nhat 6 skills
- deterministic seed de test repeatable

1. constants.py

Chua cac constant dung chung:
- NEED_NAMES:
  hunger, energy, social, fun, hygiene, bladder, health, comfort
- SKILL_NAMES:
  cooking, fitness, logic, charisma, repair, creativity
- TRAIT_NAMES:
  social, loner, ambitious, lazy, neat, messy, frugal, generous,
  creative, hot_headed
- WEEKDAYS:
  Mon Tue Wed Thu Fri Sat Sun
- SCHEMA_VERSION = 2
- MAX_EVENTS = 200

2. models.py

Tao dataclass:

Relationship:
- target_id: str
- friendship: float
- romance: float
- conflict: float
- familiarity: float
- last_interaction_tick: int

Memory:
- tick: int
- kind: str
- text: str
- strength: float
- related_person_id: str | None = None

Person:
- id: str
- name: str
- age: int
- household_id: str
- home_id: str
- money: float
- traits: list[str]
- skills: dict[str, float]
- needs: dict[str, float]
- mood: str
- job_id: str | None
- relationships: dict[str, Relationship]
- inventory: dict[str, int]
- memories: list[Memory]
- current_action: str
- action_timer: int
- location_id: str
- alive: bool

Household:
- id: str
- name: str
- funds: float
- home_id: str
- members: list[str]
- inventory: dict[str, int]
- bills_due: float

Home:
- id: str
- name: str
- capacity: int
- comfort: float
- cleanliness: float
- rent_per_day: float
- appliances: dict[str, str]

Job:
- id: str
- title: str
- salary_per_day: float
- required_skill: str
- skill_gain: float
- start_hour: int
- end_hour: int
- work_days: list[int]
- promotion_threshold: float
- promotion_job_id: str | None

Location:
- id: str
- name: str
- kind: str
- open_hour: int
- close_hour: int
- activities: list[str]
- comfort_bonus: float

ActionCandidate:
- action: str
- score: float
- duration: int
- target_id: str | None
- location_id: str | None
- reasons: list[str]

WorldEvent:
- tick: int
- day: int
- hour: int
- type: str
- message: str
- actor_id: str | None = None
- target_id: str | None = None
- severity: str = "info"

WorldState:
- tick: int
- hour: int
- day: int
- weekday: int
- rng_seed: int
- people: dict[str, Person]
- households: dict[str, Household]
- homes: dict[str, Home]
- jobs: dict[str, Job]
- locations: dict[str, Location]
- events: list[WorldEvent]
- global_flags: dict[str, str]
- metrics: dict[str, float]

Moi dataclass can co serialize/deserialize helper hoac dung ham rieng trong
persistence.py. Tranh circular import.

3. catalog.py

Chua catalog deterministic:
- create_jobs()
- create_homes()
- create_locations()
- default_people_specs()
- default_household_specs()

Catalog phai giup world.py tao world mac dinh ma khong nhung data lon vao
simulation.py.

4. rules.py

Tao rule functions pure:

clamp(value, min_value=0.0, max_value=100.0)

clamp_needs(needs)
- tra ve dict moi, moi need trong 0..100

average_needs(person)

need_pressure(person)
- tra ve dict need -> urgency 0..1

calculate_mood(person)
- neu health < 25: "sick"
- neu hunger < 20 hoac bladder < 15: "distressed"
- neu energy < 25: "tired"
- neu social < 25: "lonely"
- neu fun < 25: "bored"
- neu conflict cao voi gan day co interaction: "tense"
- neu average needs > 75 va conflict thap: "happy"
- neu logic hoac creativity dang tang gan day co the "focused"
- con lai "neutral"

decay_needs(person, hour, home_comfort=0.0)
- hunger, bladder, hygiene giam moi tick
- energy giam nhanh khi thuc khuya hoac lam viec
- social va fun giam cham
- comfort bi anh huong boi home/location
- health giam neu hunger/energy/hygiene qua thap

apply_trait_modifier(person, base_score, action)
- ambitious tang diem work/study
- lazy tang sleep/relax, giam work
- social tang socialize/party
- loner giam socialize nhung tang solo_play
- neat tang clean
- messy giam clean
- frugal giam buy_groceries
- generous tang help_neighbor/socialize

is_work_time(person, world)

world_time_label(world)

5. relationships.py

Tao functions:

ensure_relationships(world)
- dam bao moi person co Relationship den moi person khac

adjust_relationship(world, actor_id, target_id, friendship_delta=0.0,
romance_delta=0.0, conflict_delta=0.0, familiarity_delta=0.0)
- update hai chieu hop ly
- clamp 0..100

best_social_target(world, actor)
- chon target dua tren familiarity/friendship va conflict
- deterministic, khong random lung tung

relationship_summary(person)
- tra ve dict gom friend_count, rival_count, close_friend_id neu co

6. actions.py

Tao action effect functions. Moi action phai co behavior testable.

Required actions:
- eat
- cook
- sleep
- nap
- shower
- use_bathroom
- work
- study_skill
- socialize
- argue
- clean_home
- repair_appliance
- buy_groceries
- take_medicine
- host_party
- relax
- solo_play
- help_neighbor
- idle

Tao:
apply_action(world, person_id, candidate)

Rules:
- Action khong duoc lam need vuot ngoai 0..100 sau khi clamp.
- work tang money hoac household funds, giam energy/fun/hygiene, tang skill job.
- cook can groceries hoac money; tao meal inventory neu thanh cong.
- eat uu tien meal/groceries, neu khong co thi ton money.
- socialize tang friendship/familiarity/social cho hai nguoi.
- argue tang conflict, co the giam friendship, tao memory.
- clean_home tang cleanliness va hygiene nhe.
- repair_appliance can repair skill, co the fix appliance broken.
- buy_groceries giam household funds hoac person money, tang groceries.
- take_medicine tang health neu co medicine hoac ton money.
- host_party tang social/fun nhung ton household funds va lam home cleanliness giam.
- help_neighbor tang friendship, generous trait tang effect.

Moi action nen add WorldEvent ngan gon.

7. autonomy.py

Tao scoring planner:

build_action_candidates(world, person_id) -> list[ActionCandidate]
choose_action(world, person_id) -> ActionCandidate

Yeu cau:
- Khong chi la if/elif don gian. Phai tao nhieu candidate voi score.
- Score dua tren:
  - need pressure
  - work schedule
  - traits
  - money/household funds
  - health
  - relationship state
  - home cleanliness/appliance status
  - location open/closed
- Neu hunger rat thap, eat/cook phai thang.
- Neu dang gio lam va co job, work phai co diem cao tru khi health qua thap.
- Neu hygiene/bladder rat thap, shower/use_bathroom phai thang.
- Neu social rat thap, socialize/host_party/help_neighbor phai co diem cao.
- Neu appliance broken va repair skill kha, repair_appliance phai co diem cao.
- Neu no candidate hop le, fallback idle.

Planner phai deterministic: cung world seed va state thi chon cung action.

8. economy.py

Tao:

apply_daily_bills(world)
- moi ngay them/thu rent va bills
- neu household funds khong du, bills_due tang va mood/comfort bi anh huong

pay_for_item(world, person, household, amount)
- uu tien household funds, neu khong du thi person money
- tra True/False

apply_work_income(world, person)
- tra luong theo job
- tang skill
- neu skill vuot promotion_threshold va co promotion_job_id thi promote

household_net_worth(world, household_id)

9. events.py

Tao:

add_event(world, type, message, actor_id=None, target_id=None, severity="info")
- giu event list khong qua MAX_EVENTS

deterministic_roll(world, salt)
- tra float 0..1 dua tren rng_seed, tick, day, salt

trigger_daily_events(world)
- it nhat cac event:
  - rent_due
  - grocery_discount
  - appliance_break
  - neighborhood_party
  - minor_illness
  - job_deadline
  - surprise_bonus
- event phai deterministic theo seed
- event co anh huong nho den world, khong chi log text

remember(person, tick, kind, text, strength, related_person_id=None)
- them Memory va gioi han moi person giu toi da 20 memories

10. world.py

Tao:

create_default_world(seed=42) -> WorldState
- dung catalog
- tao people/households/homes/jobs/locations
- assign people vao households va homes
- assign it nhat 6 nguoi co job
- tao relationship ban dau giua moi nguoi
- tao inventory ban dau
- add event "world_created"

get_person(world, person_id)
get_household(world, household_id)
get_home(world, home_id)
get_job(world, job_id)
get_location(world, location_id)

validate_world(world) -> list[str]
- tra list errors, empty la ok
- kiem population, household membership, home capacity, needs range,
  relationship symmetry co ban

11. simulation.py

Tao class Simulation:

__init__(world)
step()
run(ticks)
summary()
person_report(person_id)
household_report(household_id)

Moi step:
- tang tick
- update hour/day/weekday
- neu sang ngay moi thi apply_daily_bills va trigger_daily_events
- voi moi person alive:
  - decay needs
  - choose_action
  - apply_action
  - calculate_mood
  - update metrics
- add event summary moi 24 ticks

run(ticks):
- goi step ticks lan
- tra summary cuoi

summary() tra dict gom:
- day
- hour
- weekday
- population
- household_count
- average_money
- average_household_funds
- average_needs
- mood_counts
- action_counts
- richest_household_id
- lowest_need_person_id
- recent_events
- validation_errors

12. persistence.py

Tao:

save_world(world, path)
load_world(path)
world_to_dict(world)
world_from_dict(data)
migrate_world_data(data)

Yeu cau:
- JSON stdlib only.
- File luu co schema_version.
- load_world co the doc lai file do save_world tao.
- migrate_world_data chap nhan dict schema_version 1 toi thieu va nang len v2.
- Sau load, dataclass type phai dung, khong de nested dict thay dataclass.

13. reporting.py

Tao:

summary_text(summary)
event_timeline(world, limit=10)
leaderboard(world, metric)
debug_person_table(world)

Output terminal ngan gon, de doc.

14. cli_demo.py

Khi chay:

python society_sim_complex/cli_demo.py

No phai:
- tao world default seed=123
- validate world va in loi neu co
- chay simulation 7 ngay, moi ngay 24 ticks
- in summary sau moi 12 ticks
- in event timeline ngan
- save file society_sim_complex/savegame_complex.json
- load lai file
- chay tiep 12 ticks sau load
- in summary sau load
- in marker:

SOCIETY_SIM_COMPLEX_DEMO_OK

Nen co main() tra int de test import duoc.

15. test_society_sim_complex.py

Khong dung pytest.
Dung assert thuong va main test runner don gian.

Bat buoc co it nhat cac test:
- create_default_world tao du counts toi thieu.
- validate_world(world) tra empty list.
- moi person co day du NEED_NAMES trong 0..100.
- relationships duoc tao cho moi cap person khac nhau.
- choose_action uu tien eat/cook khi hunger rat thap.
- choose_action uu tien work trong gio lam neu person co job va health khong thap.
- traits co anh huong den score: ambitious lam work/study cao hon, lazy lam sleep/relax cao hon.
- social action lam friendship hoac familiarity tang.
- argue lam conflict tang.
- work lam money/funds hoac skill tang.
- daily bills lam household funds/bills_due thay doi.
- appliance_break deterministic voi cung seed/tick.
- events khong vuot MAX_EVENTS sau run dai.
- save/load giu population, tick, day, nested dataclass va relationships.
- migrate_world_data xu ly schema_version 1 toi thieu.
- Simulation.run(24 * 7) khong crash.
- needs luon nam trong 0..100 sau 7 ngay.
- summary co du key bat buoc.
- reporting functions tra string/list khong rong.
- cli_demo.main() chay duoc va tra 0.

Khi chay:

python society_sim_complex/test_society_sim_complex.py

Neu pass, phai in:

SOCIETY_SIM_COMPLEX_TESTS_OK

Quality gates:
- Khong de TODO, pass placeholder, hoac ham rong.
- Khong swallow exception trong test.
- Khong fake test bang cach chi print marker.
- Test phai that su goi simulation, persistence, autonomy, economy, events.
- Code nen co type hints co ban.
- Function phai nho, module boundary ro.
- Business rules nen nam trong rules/economy/events/actions, khong don het vao
  simulation.py.

Quy trinh lam viec bat buoc:

1. Neu can phan tich dai, ghi phan tich thanh artifact/file ngan trong
   `society_sim_complex/` hoac su dung artifact system cua Software Factory.
   JSON tool call phai ngan, khong nhet phan tich dai vao JSON.
2. Dung filesystem.create_directory tao `society_sim_complex`.
3. Tao tung file bang file_editor.file_editor_write_lines. Moi phan tu trong
   `lines` la dung mot dong vat ly cua file. Moi phan tu phai la JSON string
   dung dau nhay kep ben ngoai. Trong code Python, uu tien dung nhay don de
   tranh escape JSON. Khong nhet ca file vao mot string dai co `\n`.
4. Sau khi tao xong, chay python.run_python voi path
   "society_sim_complex/test_society_sim_complex.py".
5. Neu test loi, doc stdout/stderr, sua dung file lien quan, chay lai.
6. Sau khi test pass, chay python.run_python voi path
   "society_sim_complex/cli_demo.py".
7. Final bang tieng Viet, bao:
   - danh sach file da tao
   - tinh nang da co
   - test da chay
   - stdout test
   - demo co chay duoc khong
   - save/load file nam o dau
   - gioi han hien tai cua project
   - buoc phat trien tiep theo neu muon len ban phuc tap hon

Acceptance markers:
- Test stdout phai co `SOCIETY_SIM_COMPLEX_TESTS_OK`.
- Demo stdout phai co `SOCIETY_SIM_COMPLEX_DEMO_OK`.

Goi y command test khi noi LLM:

python main_langgraph.py prompts/the_sims_complex_prompt.md

Hoac chay qua Software Factory truoc:

python run_software_factory_demo.py --task-file prompts/the_sims_complex_prompt.md

Sau do dua implementation spec sinh ra cho Company Agents real mode.
