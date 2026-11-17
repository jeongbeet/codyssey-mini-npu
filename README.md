# Mini NPU Simulator

입력 패턴과 두 필터의 MAC(Multiply-Accumulate) 점수를 계산하고, 큰 점수의
필터를 선택하는 Python 콘솔 애플리케이션입니다. 사용자 입력, JSON 일괄 분석,
허용오차에 따른 동점 판정, 크기별 성능 측정, 실패 원인 요약을 제공합니다.

MAC은 NumPy 등 외부 라이브러리 없이 이중 반복문으로 구현했습니다.
`main.py`는 실행 진입점이며, 실제 구현은 `src/` 패키지에 있습니다.
실행할 때 `main.py`, `src/`, `data.json`을 같은 저장소 안에 유지하세요.

## 실행 방법

- 필요 환경: Python 3.10 이상.
- 검증 환경: Python 3.12.14, Linux x86_64.
- 의존성: Python 표준 라이브러리만 사용하므로 추가 패키지 설치가 필요 없습니다.
- 아래 명령은 저장소 루트에서 실행합니다. 환경에 따라 `python` 대신 `python3`를 사용하세요.

대화형 메뉴:

~~~bash
python main.py
~~~

~~~text
Mini NPU Simulator
1. 사용자 입력 (3×3)
2. data.json 분석
0. 종료
~~~

각 분석이 끝나면 메뉴로 돌아옵니다. 메뉴에서 잘못된 값을 입력하면 다시 선택할 수 있습니다.

메뉴를 거치지 않고 한 번 실행:

~~~bash
python main.py --mode manual
python main.py --mode json
python main.py --mode json --data data.json --epsilon 1e-9 --repeats 1000
~~~

같은 프로그램을 패키지로 실행할 수도 있습니다.

~~~bash
python -m src --mode json
python main.py --help
~~~

기본 JSON 경로는 실행 위치와 관계없이 저장소의 `data.json`입니다.
`--data`로 지정한 상대 경로는 현재 작업 디렉터리를 기준으로 해석합니다.

| 옵션 | 기본값 | 의미 |
|---|---|---|
| `--mode` | 대화형 메뉴 | `manual`: 3×3 입력, `json`: JSON 분석 |
| `--data` | 저장소의 `data.json` | 분석할 JSON 파일 |
| `--epsilon` | `1e-9` | 동점 판정에 사용하는 양의 유한한 절대오차 |
| `--repeats` | `100` | 필터별 측정 횟수. 최소 10회 |

제공된 데이터에는 동점으로 인해 FAIL인 케이스가 3개 있습니다.
따라서 `--mode json`으로 실행하면 결과를 모두 출력한 후 **종료 코드 1**을 반환합니다.

| 종료 코드 | 의미 |
|---|---|
| `0` | 사용자 입력 모드 완료, JSON 전체 PASS, 또는 메뉴에서 정상 종료 |
| `1` | JSON 분석 완료 후 FAIL인 케이스가 하나 이상 존재 |
| `2` | 잘못된 옵션, 파일·최상위 스키마 오류, 미완료 행렬 입력, 사용자 모드 연산 오류 |
| `130` | 사용자가 Ctrl+C로 중단 |

개별 케이스의 크기·라벨·필터 오류는 해당 케이스의 FAIL로 집계합니다.
대화형 메뉴에서는 파일 오류를 안내한 후에도 다음 모드를 선택할 수 있습니다.

## 사용자 입력 모드: 3×3

실행 순서는 다음과 같습니다.

1. 필터 A를 3줄로 입력합니다.
2. 필터 B를 3줄로 입력합니다.
3. 저장된 필터 A와 B를 출력하여 확인합니다.
4. 패턴을 3줄로 입력합니다.
5. 두 MAC 점수와 각 MAC 호출 시간(ms)을 계산합니다.
6. A/B/UNDECIDED 판정과 3×3 반복 성능 측정 결과를 출력합니다.

각 줄에는 공백으로 구분한 숫자 3개가 필요합니다.
각 행렬은 정확히 3행을 받으며, 행별 숫자 개수나 숫자 변환에 문제가 있으면
해당 행을 다시 입력합니다. 정수·소수·음수를 지원하고 NaN과 무한대는 거부합니다.
입력이 중간에 끝나면 오류 메시지를 출력하고 종료합니다.

예시 필터 A:

~~~text
0 1 0
1 1 1
0 1 0
~~~

예시 필터 B:

~~~text
1 0 1
0 1 0
1 0 1
~~~

예시 패턴:

~~~text
0 1 0
1 1 1
0 1 0
~~~

이 입력의 결과는 **A 점수 5, B 점수 1, 판정 A**입니다.
시간은 실행 시 측정한 값으로 출력합니다.
동점이면 `UNDECIDED (판정 불가)`를 출력합니다.
사용자 입력 모드에는 expected가 없으므로 PASS/FAIL 정답 비교는 수행하지 않습니다.

## JSON 분석 모드

첨부된 원본 `data.json`을 내용 변경 없이 포함했습니다.
최상위에는 `meta`, `filters`, `patterns`가 있으며, `meta`는 계산에 사용하지 않습니다.
`filters`와 비어 있지 않은 `patterns` 객체가 필수입니다.

| 구분 | 제공 데이터의 구조 |
|---|---|
| `filters.size_5` | `cross`, `x`에 각각 5×5 필터 |
| `filters.size_13` | `cross`, `x`에 각각 13×13 필터 |
| `filters.size_25` | `cross`, `x`에 각각 25×25 필터 |
| `patterns.size_5_1`, `patterns.size_5_2` | `input`: 5×5 패턴, `expected`: 정답 라벨 |
| `patterns.size_13_1`, `patterns.size_13_2` | `input`: 13×13 패턴, `expected`: 정답 라벨 |
| `patterns.size_25_1`, `patterns.size_25_2` | `input`: 25×25 패턴, `expected`: 정답 라벨 |

케이스 키는 `size_{N}_{idx}` 형식입니다. N은 양의 정수이고 idx는 숫자입니다.
키에서 추출한 N으로 `filters["size_N"]`을 선택하며,
패턴과 두 필터 모두 정확히 N행·N열인지 검사합니다.
행렬은 2차원 리스트로 저장하므로 `matrix[row][col]`로 값을 읽거나 수정할 수 있습니다.
실수로 변환할 수 있는 범위의 정수·실수만 허용하며 문자열 숫자, bool, NaN, 무한대는 거부합니다.

라벨은 입력 위치에 관계없이 아래 표에 따라 정규화하며, 앞뒤 공백과 대소문자도 처리합니다.

| 원본 라벨 | 내부 표준 라벨 |
|---|---|
| expected의 `+` | `Cross` |
| 필터의 `cross`, 표준 표기 `Cross` | `Cross` |
| expected/필터의 `x`, 표준 표기 `X` | `X` |

정규화 후 Cross와 X 필터가 모두 있어야 합니다.
지원하지 않는 라벨이나 정규화 후 중복된 필터 라벨도 검증 오류입니다.
`UNDECIDED`는 계산 결과의 동점 상태이며 expected의 정답 라벨로 허용하지 않습니다.

JSON 모드의 흐름:

1. 파일을 읽고 최상위 스키마를 검증합니다.
2. 케이스 키에서 크기를 추출하고 필터를 선택합니다.
3. expected와 필터 이름을 정규화하고 행렬 크기·값을 검증합니다.
4. Cross/X 점수를 계산하고 epsilon 정책으로 판정합니다.
5. 정규화한 expected와 판정 결과를 비교하여 PASS/FAIL을 출력합니다.
6. 3×3·5×5·13×13·25×25 성능 표를 출력합니다.
7. 전체 테스트 수·통과 수·실패 수 및 실패 식별자·사유를 요약합니다.

개별 케이스의 검증 오류나 MAC 결과의 오버플로는 FAIL로 남기고 다음 케이스를 계속 처리합니다.
연산하지 못한 케이스의 점수·판정은 `-`로 표시하여 동점과 구별합니다.
파일 없음, JSON 문법 오류, 최상위 필수 객체 누락, 빈 patterns는 전체 로드 오류로 안내합니다.
0개 케이스를 실행하고 성공한 것으로 보고하지 않습니다.

## MAC과 epsilon 정책

점수는 다음과 같습니다.

~~~text
score = Σ(row=0..N-1) Σ(col=0..N-1) pattern[row][col] × kernel[row][col]
~~~

`src/mac.py`에서 검증된 두 행렬을 이중 반복문으로 순회하고,
`total += pattern[row][col] * kernel[row][col]`로 점수를 누적합니다.
0인 원소도 순회하며, 필터의 배율이나 점수를 임의로 정규화하지 않습니다.

~~~python
if abs(score_a - score_b) < epsilon:
    decision = "UNDECIDED"
else:
    decision = label_a if score_a > score_b else label_b
~~~

- 기본 epsilon은 절대오차 `1e-9`입니다.
- 차이가 epsilon보다 작으면 동점입니다. 정확히 같으면 큰 점수를 선택합니다.
- 판정에는 반올림 전 float 값을 사용합니다.
- 화면 점수는 최대 12자리 유효숫자로 표시하고, 동점 사유에는 점수 차이를 최대 17자리로 표시합니다.
- 사용자 모드는 A/B, JSON 모드는 Cross/X를 판정 라벨로 사용합니다.
- expected는 점수 계산이나 판정에 사용하지 않고, 판정 후 정답 비교에만 사용합니다.
- JSON에서 UNDECIDED는 expected인 Cross/X와 다르므로 FAIL입니다.
- epsilon을 변경하면 동점 여부와 집계 결과가 달라질 수 있습니다.

## 성능 측정 방법

`time.perf_counter_ns()`로 MAC 함수 호출 구간만 측정합니다.
각 필터를 한 번 워밍업한 뒤 필터별 최소 10회, 기본 100회를 측정합니다.
입력, 출력, 파일 읽기, 행렬 생성, 검증, 워밍업은 측정 시간에 포함하지 않습니다.

~~~text
평균 시간(ms) = 모든 측정 구간의 합(ns) / (필터 수 × 반복 횟수) / 1,000,000
~~~

두 필터를 각각 측정해 합산하므로 표의 시간은 **필터 하나에 대한 MAC 함수 1회 평균**입니다.
사용자 모드에서 따로 출력하는 A/B 시간은 각각 단일 호출의 실측값입니다.

JSON 모드에서는 크기별로 계산 가능한 첫 번째 케이스를 성능 측정에 사용합니다.
동점이나 정답 불일치인 케이스도 정상적으로 점수가 계산되었다면 사용할 수 있습니다.
JSON에 없는 3×3, 또는 사용할 수 있는 케이스가 없는 크기는 고정된 측정용 행렬을 생성합니다.
측정용 생성 데이터는 결과에 출처를 표시하며 JSON 테스트 합계에 포함하지 않습니다.

N²는 곱셈 후 누적하는 MAC 단계의 개수입니다.
곱셈과 덧셈을 각각 별도 산술 연산으로 세면 필터 하나에 2N²회입니다.
두 필터를 비교하는 판정 한 건은 2N² MAC 단계를 수행합니다.

## 결과 리포트

### 제공 데이터의 실제 판정

다음 명령을 Python 3.12.14 / Linux x86_64에서 실행했습니다.

~~~bash
python3 main.py --mode json --epsilon 1e-9 --repeats 1000
~~~

| 케이스 | Cross 점수* | X 점수* | 판정 | expected 정규화 | 결과 |
|---|---:|---:|---|---|---|
| `size_5_1` | 0.9 | 0.9 | UNDECIDED | X | FAIL |
| `size_5_2` | 8.9 | 0.1 | Cross | Cross | PASS |
| `size_13_1` | 0.3 | 14.7 | X | X | PASS |
| `size_13_2` | 7.5 | 7.5 | UNDECIDED | Cross | FAIL |
| `size_25_1` | 4.9 | 4.9 | UNDECIDED | X | FAIL |
| `size_25_2` | 52.9 | 0.1 | Cross | Cross | PASS |

\* 점수 표시는 반올림한 값이며 판정에는 반올림 전 값을 사용했습니다.

~~~text
전체 테스트: 6 | PASS: 3 | FAIL: 3
~~~

### 실제 성능 측정

각 필터 1,000회, 크기별 총 2,000회 호출의 평균입니다.
2026-11-17 클라우드 환경에서 측정한 한 번의 실행 결과이며, 실행마다 값은 달라질 수 있습니다.

| 크기 | MAC 1회 평균(ms) | MAC 단계 N² | 측정 데이터 |
|---|---:|---:|---|
| 3×3 | 0.000649 | 9 | 별도 생성한 3×3 측정용 패턴·필터 |
| 5×5 | 0.001350 | 25 | `size_5_1` |
| 13×13 | 0.007111 | 169 | `size_13_1` |
| 25×25 | 0.025397 | 625 | `size_25_1` |

### 실패 원인 및 복잡도 분석

1. 제공된 데이터의 패턴은 크기별 2개씩 총 6개이며, 6개 모두 스키마 검증과 MAC 계산을 완료했습니다.
2. 필터·패턴의 행·열 수는 모두 일치하므로 이번 실행에는 크기 오류로 인한 FAIL이 없습니다.
3. 원본 expected의 `+`, `x`와 필터 이름 `cross`, `x`는 Cross/X로 정규화했습니다.
4. 정규화를 통해 표기가 다른 동일 라벨을 같게 비교하며, 라벨 불일치 자체로 발생하는 오판을 방지했습니다.
5. `size_5_1`의 점수는 Cross=0.9, X=0.8999999999999999이며 차이는 약 `1.1102230246251565e-16`입니다.
6. 이 차이는 epsilon보다 작아 UNDECIDED이며, expected=X와 일치하지 않아 FAIL입니다.
7. `size_13_2`의 점수는 Cross=7.499999999999997, X=7.5이며 차이는 약 `2.6645352591003757e-15`입니다.
8. 이 케이스도 epsilon 기준 동점이므로 UNDECIDED이며, expected=Cross와 일치하지 않아 FAIL입니다.
9. `size_25_1`의 점수는 Cross=4.9, X=4.899999999999999이며 차이는 약 `1.7763568394002505e-15`입니다.
10. 이 케이스 역시 UNDECIDED이며, expected=X와 일치하지 않아 FAIL입니다.
11. 세 차이는 부동소수점 표현·누적 오차 수준입니다. 단순 대소 비교로 특정 라벨을 선택하지 않도록 epsilon 정책을 적용했습니다.
12. 따라서 세 실패는 유효한 입력에서 동점 판정과 expected가 불일치한 결과입니다. expected에 맞추기 위해 필터나 판정 규칙을 바꾸지 않았습니다.
13. `size_5_2`, `size_13_1`, `size_25_2`는 충분한 점수 차이가 있으며 각각 Cross, X, Cross로 판정되어 PASS입니다.
14. JSON 테스트 집계는 실제 패턴 6개만 포함하며, 3×3 측정용 데이터와 성능 반복 호출은 포함하지 않습니다.
15. MAC 함수는 N행마다 N열을 모두 처리하므로 시간 복잡도는 O(N²)입니다.
16. 두 필터의 점수를 계산하면 2N² MAC 단계를 수행하지만 상수 계수를 제외한 복잡도는 O(N²)입니다.
17. 크기가 N_k인 K개 케이스의 검증·판정 시간은 전체 입력량에 비례하는 O(ΣN_k²)이며, 파일 파싱과 결과 출력 시간은 별도입니다.
18. 반복 성능 측정은 두 필터와 반복 횟수 R에 대해 O(R·ΣN²)이고, 표에는 반복 합계가 아닌 호출 1회 평균을 기록했습니다.
19. MAC 함수는 누적 변수와 반복 인덱스만 사용하므로 이미 저장된 입력을 제외한 추가 공간은 O(1)입니다.
20. 행렬 한 개의 저장·검증 복사 공간은 O(N²)이며, 전체 JSON은 파일 내용과 행렬들을 메모리에 보관합니다.
21. 작은 행렬에서는 타이머·함수 호출 비용과 시스템 부하의 영향이 상대적으로 커서 실측 시간의 비율이 N² 비율과 정확히 같지는 않습니다.
22. 자동화 테스트 32개는 모두 통과했습니다. 이 검증에는 제공 데이터의 3개 FAIL을 올바르게 보고하는 동작도 포함됩니다.

## 파일 구조와 핵심 함수

~~~text
codyssey-mini-npu/
├── README.md
├── main.py
├── data.json
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── models.py
│   ├── validation.py
│   ├── data_loader.py
│   ├── input_handler.py
│   ├── mac.py
│   ├── runner.py
│   ├── benchmark.py
│   └── report.py
└── tests/
    ├── __init__.py
    ├── test_mac.py
    ├── test_validation.py
    ├── test_data_loader.py
    ├── test_runner.py
    ├── test_benchmark.py
    └── test_cli.py
~~~

| 파일 | 핵심 함수·구조 | 역할 |
|---|---|---|
| `main.py`, `src/__main__.py` | `main()` 호출 | 스크립트·패키지 진입점 |
| `src/cli.py` | `main()` | 옵션, 메뉴, 종료 코드 |
| `src/models.py` | `PreparedCase`, `CaseResult`, `BenchmarkResult` | 검증된 입력, 케이스 결과, 성능 결과 |
| `src/validation.py` | `validate_matrix()`, `parse_case_size()` | 행렬·키 검증 |
| `src/validation.py` | `validate_epsilon()`, `validate_repeats()` | 비교·측정 정책 검증 |
| `src/data_loader.py` | `load_dataset()`, `normalize_label()`, `prepare_case()` | 파일 로드·라벨 정규화·필터 선택 |
| `src/input_handler.py` | `read_matrix()` | 콘솔 행 단위 입력과 재입력 |
| `src/mac.py` | `mac_score()`, `decide()` | 반복문 MAC·epsilon 판정 |
| `src/runner.py` | `evaluate_case()`, `analyze_dataset()` | 케이스 평가·실패 격리 |
| `src/runner.py` | `run_manual_mode()`, `run_json_mode()` | 모드별 실행 순서 |
| `src/benchmark.py` | `make_benchmark_fixture()`, `benchmark_mac()` | 측정 데이터 생성·반복 시간 측정 |
| `src/report.py` | `print_case_result()`, `print_benchmarks()`, `print_summary()` | 개별 결과·성능·실패 목록 출력 |

## 자동화 검증

~~~bash
python -m unittest discover -s tests -v
~~~

검증 결과: **32개 테스트 통과**.

- 음수·소수 MAC과 3×3·5×5·13×13·25×25 연산.
- epsilon보다 작은 차이, 정확한 경계, 큰 차이 및 양쪽 점수 우위.
- 라벨 정규화, 중복 라벨, 누락된 필터, 잘못된 행렬·케이스 키.
- NaN·무한대·bool·숫자 범위 오류와 MAC 오버플로.
- 잘못된 케이스 이후 정상 케이스를 계속 처리하는 동작.
- 제공 데이터의 6개 판정과 전체 3 PASS / 3 FAIL.
- 워밍업 제외와 필터 1회 기준 평균 시간 계산.
- 콘솔 재입력, 사용자 모드의 승리·동점, JSON 모드, 메뉴 재선택.
- 파일 오류, 미완료 입력, 옵션 검증, 종료 코드.
- 저장소 밖에서 실행해도 기본 데이터 경로가 유지되는 동작과 `python -m src` 실행.
