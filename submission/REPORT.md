# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đinh Đức Long
- **MSSV:** 2A202602633
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/longdinhduc123/K4-L3B-Day13-DinhDucLong-2A202602633-Monitoring-LLMOps
- **Commit SHA cuối:** 090d603  
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602633`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/pytest.txt` |
| Log validator | `evidence/log-validator.txt` |
| Dashboard validator | `evidence/dashboard-validator.txt` |
| Pytest cuối (commit + pass) | `evidence/01-pytest.png` |
| Log validator (score >= 80) | `evidence/02-log-validator.png` |
| Dashboard validator (6/6 panel) | `evidence/03-dashboard-validator.png` |
| Structured log (ID: `req-1a2b3c4d`) | `evidence/04-structured-log.png` |
| PII redaction log | `evidence/05-pii-redaction.png` |
| Langfuse trace list (>= 10 traces) | `evidence/06-trace-list.png` |
| Trace waterfall & tree | `evidence/07-trace-waterfall.png` |
| Observation metadata & generation | `evidence/08a-metadata.png`, `evidence/08b-generation.png` |
| Prompt versions (v1, v2) | `evidence/09-prompt-versions.png` |
| Prompt promote & rollback | `evidence/10a-promote.png`, `evidence/10b-rollback.png` |
| Dashboard overview (6 panels) | `evidence/11-dashboard-overview.png` |
| Incident metric (dashboard sau challenge) | `evidence/12-incident-metric.png` |
| Incident log (request bất thường) | `evidence/13-incident-log.png` |
| Incident trace (Langfuse span bất thường) | `evidence/14-incident-trace.png` |


## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt điểm tuyệt đối, đầy đủ metadata & 0 PII leak |
| `validate_dashboard.py` | 6/6 panel hợp lệ | 6/6 panel hợp lệ | Đạt trọn vẹn dashboard contract |
| `pytest` | 22 passed | 24 passed | 100% passed (bổ sung test PII CCCD & Thẻ tín dụng) |
| Số traces hợp lệ | 0 | > 100 traces | Đầy đủ quan hệ Root → Retrieval → Generation |
| Số PII leak | 0 | 0 | Scrub hoàn toàn 4 nhóm PII trước khi log |
| Latency P95 / TTFT P95 | ~415ms / N/A | 172ms / 50ms | Đo qua baseline load_test.py |
| Retrieval success rate | 100% | 100% | Đạt mục tiêu khả dụng của hệ thống |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong [CorrelationIdMiddleware](../app/middleware.py), gọi `clear_contextvars()` để xóa context cũ tránh rò rỉ giữa các request, nhận header `x-request-id` nếu client truyền lên hoặc tự động sinh theo định dạng `req-{uuid.uuid4().hex[:8]}`. Sau đó bind vào contextvars thông qua `bind_contextvars(correlation_id=...)`, lưu vào `request.state.correlation_id` và đính kèm vào response headers `x-request-id` cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Gồm các trường hệ thống (`ts`, `level`, `service`, `event`), trường ngữ cảnh request (`correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`), cùng các trường đo lường hiệu năng/chất lượng (`latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`).
- **Cách bảo đảm PII được scrub trước khi ghi:** Cấu hình processor `scrub_event` trong chuỗi structlog processors đặt trước `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_event` duyệt qua `payload` và `event` để thay thế email, số điện thoại VN, số CCCD 12 số, số thẻ ngân hàng bằng nhãn `[REDACTED_*]` trước khi log được render thành JSON hoặc ghi xuống đĩa.
- **Cách kiểm chứng kết quả:** Chạy bộ test `pytest tests/test_pii.py` (bổ sung test cho CCCD và thẻ tín dụng), chạy `python scripts/load_test.py` sinh workload thực tế và kiểm tra bằng `python scripts/validate_logs.py` đạt điểm tối đa 100/100 (0 PII leak, 0 missing required fields, 0 missing enrichment).
- **Correlation ID tự đặt (Evidence 04):** `req-1a2b3c4d` (gồm 2 khối JSON `request_received` và `response_sent` đầy đủ metadata).
- **Correlation ID kiểm tra PII (Evidence 05):** `req-2a202633-05` (đã scrub hoàn toàn cả 4 loại PII: email, SĐT VN, CCCD, thẻ tín dụng).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Trong file `.env`, cấu hình `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` được tạo trực tiếp từ project cá nhân `day13-k4-l3b-2A202602633` trên Langfuse Cloud. Mọi trace sinh ra đều chứa `user_id_hash`, `tags=["lab", feature, model]` và `metadata.correlation_id` khớp với log cục bộ.
- **Cấu trúc root/retrieval/generation observations:**
  - Root trace: `day13-agent-request` (thiết lập qua `propagate_attributes`).
  - Observation 1: `lab-agent-run` (loại `agent`, decorate trên `LabAgent.run`).
  - Observation 2: `retrieval` (loại `retriever`, decorate trên hàm `retrieve()`, `capture_input=False, capture_output=False` để chống rò rỉ PII).
  - Observation 3: `generation` (loại `generation`, decorate trên `FakeLLM.generate()`, cập nhật `model`, `usage_details`, `cost_details` và liên kết tới prompt object qua `propagate_attributes(prompt=prompt.managed_prompt)`).
- **Cách nối trace với log:** Thông qua `correlation_id`. Trong log `data/logs.jsonl`, `correlation_id` xuất hiện ở mọi dòng log (`request_received`, `response_sent`). Trong Langfuse, `correlation_id` được ghi vào `metadata` của trace/observation. Tìm kiếm `correlation_id` trên Langfuse sẽ trỏ thẳng tới trace của request đó.
- **Prompt name:** `day13-chat` (Text prompt, chứa 3 biến bắt buộc `{{feature}}`, `{{docs}}`, `{{message}}`).
- **Version/label baseline:** Version 1, gán nhãn `baseline` và `production` ban đầu.
- **Version/label candidate:** Version 2 (thêm chỉ dẫn trả lời súc tích), gán nhãn `candidate`.
- **Trace ID của mỗi version:**
  - Baseline (v1): `7cd61c982ceef0abc717db90c74cbc23`
  - Candidate (v2): `e30bc3bda1d4ab33d87a64ccb3acbf0a`
- **Cách promote và rollback `production`:**
  - **Promote:** Trên Langfuse (Prompt Management -> `day13-chat`), gán label `production` cho Version 2 (label sẽ tự động dời từ v1 sang v2), restart API để tải prompt mới.
  - **Rollback:** Khi cần quay lại, gán lại label `production` cho Version 1. Ứng dụng chạy theo `LANGFUSE_PROMPT_LABEL=production` sẽ tự động chuyển về v1 mà không cần sửa code.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** 6 panel được định nghĩa theo [config/dashboard.yaml](../config/dashboard.yaml) gồm: Latency (P50/P95/P99, TTFT, ngưỡng 3000ms), Traffic (số lượng request theo thời gian), Errors (tỉ lệ lỗi HTTP 500 và tỉ lệ retrieval success), Cost (chi phí tích luỹ theo ngày so với giới hạn $2.5), Tokens (độ dài input/output token), và Quality (điểm chất lượng phản hồi heuristic trung bình >= 0.75).
- **SLO và lý do chọn:** Primary SLO đặt trong [config/slo.yaml](../config/slo.yaml) là `fast_successful_requests` với mục tiêu 99.5% request trong chu kỳ 28 ngày phải phản hồi thành công và có `latency_ms <= 3000ms`. Lý do: Ứng dụng hỗ trợ hỏi đáp trực tiếp (chatbot/QA) đòi hỏi phản hồi nhanh dưới 3s để người dùng không bỏ phiên, đồng thời việc trả lời lỗi (500) phá vỡ trải nghiệm dịch vụ.
- **Cách tính error budget:** Với target SLO 99.5%, error budget là $100\% - 99.5\% = 0.5\%$. Trong khoảng thời gian 28 ngày, nếu hệ thống phục vụ tổng cộng 10,000 requests thì ngân sách lỗi cho phép tối đa $10,000 \times 0.5\% = 50$ requests bị chậm quá 3s hoặc gặp lỗi.
- **Ba alert và runbook tương ứng:** Định nghĩa trong [config/alert_rules.yaml](../config/alert_rules.yaml) và tài liệu hóa tại [docs/alerts.md](../docs/alerts.md):
  1. `HighLatencyP95` (Warning, 5m): `p95(latency_ms) > 3000ms` trỏ tới [docs/alerts.md#alert-1](../docs/alerts.md#alert-1).
  2. `HighErrorRate` (Critical, 3m): `error_rate > 2%` hoặc `retrieval_success_rate < 90%` trỏ tới [docs/alerts.md#alert-2](../docs/alerts.md#alert-2).
  3. `CostBurnSpike` (Warning, 5m): `daily_cost_usd > 2.5` trỏ tới [docs/alerts.md#alert-3](../docs/alerts.md#alert-3).

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 23:26:00 – 23:28:00 (GMT+7) ngày 30/09/2026 (tương ứng 16:26:00Z – 16:28:00Z)
- **Triệu chứng từ metrics:** Trên dashboard runtime (Panel 1 - Latency percentiles and TTFT), Latency P95 tăng vọt từ mốc baseline ~172ms lên **2655ms** (P99 đạt **2656ms**), vượt qua ngưỡng cảnh báo `latency_threshold_ms: 2000` của challenge và tiếp cận sát ngưỡng SLO 3000ms. Panel 2 (Traffic) ghi nhận 5 requests của feature `monitoring` chạy đồng thời trong đợt này.
- **Log line và correlation ID liên quan:** `correlation_id: req-5d10544c`. Dòng log `response_sent` tương ứng có `event="response_sent"`, `feature="monitoring"`, `model="claude-sonnet-4-5"`, `latency_ms=2656`, `ttft_ms=50`, `tokens_in=34`, `tokens_out=137`, `cost_usd=0.002157`, `tool_name="retrieval"`, `tool_success=true`, `ts="2026-09-30T16:27:12.964147Z"`.
- **Trace ID và span gây ảnh hưởng:** Trace ID `cba778709bf1ea6370b79cafe1c4412d` trên Langfuse project `day13-k4-l3b-2A202602633`. Span gây ảnh hưởng là `retrieval` (loại `retriever`) kéo dài **2.501s** (chiếm ~94% tổng latency 2.663s của toàn bộ trace), trong khi span `generation` hoạt động bình thường chỉ mất **0.152s**.
- **Root cause:** Module Retrieval (Mock RAG) bị nghẽn độ trễ nghiêm trọng do sự cố `rag_slow` inject độ trễ tĩnh 2.5 giây (`time.sleep(2.5)`) vào hàm `retrieve()`, khiến thời gian phản hồi của toàn bộ pipeline QA/Monitoring bị chậm tail latency.
- **Fix action:** Tắt incident bằng lệnh `python scripts/inject_incident.py --disable` (trả `rag_slow=false`), kiểm tra lại kết nối và cache retrieval, xác nhận độ trễ trung bình quay về mức bình thường (~170ms).
- **Preventive measure:** Bổ sung alert rule giám sát riêng cho độ trễ retrieval (`p95(retrieval_latency_ms) > 1000ms` kéo dài 3 phút), áp dụng cơ chế timeout 1.5s và fallback trả lời tổng quát nếu retrieval không phản hồi, tích hợp semantic cache để giảm thiểu truy vấn trực tiếp vào vector database.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Cấu hình `clear_contextvars()` trong middleware `CorrelationIdMiddleware` trước khi bind `correlation_id` mới vào contextvars. Lý do: Python ASGI server tái sử dụng thread/task có thể gây rò rỉ ngữ cảnh request cũ sang request mới, việc clear triệt để bảo đảm tính toàn vẹn của dữ liệu telemetry và correlation ID.
- **Một lỗi/blocker đã gặp:** Thứ tự xử lý PII scrubbing có thể làm sai lệch định dạng nếu regex bao quát quá rộng (ví dụ chuỗi 16 số thẻ thanh toán và 12 số CCCD dễ trùng khớp nếu không có boundary chuẩn).
- **Cách tìm nguyên nhân và xử lý:** Thiết kế pipeline regex theo thứ tự ưu tiên từ cụ thể đến tổng quát: Thẻ ngân hàng (16 số) -> CCCD (12 số) -> Điện thoại VN (10 số đầu số hợp lệ) -> Email. Bổ sung test case phủ toàn bộ các mẫu dữ liệu trong `tests/test_pii.py` và kiểm tra qua `validate_logs.py` đạt 100/100.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics (Dashboard):** Cung cấp góc nhìn vĩ mô giúp phát hiện *khi nào có sự cố* và *mức độ ảnh hưởng ra sao* (ví dụ: P95 latency tăng từ 172ms lên 2655ms lúc 16:27Z).
  - **Logs (Structured Logs):** Lọc theo khoảng thời gian và feature bị ảnh hưởng để tìm ra *request cụ thể nào gặp lỗi* và trích xuất `correlation_id` (`req-5d10544c`).
  - **Traces (Distributed Tracing):** Sử dụng `correlation_id` tra cứu trên Langfuse để quan sát cây phân cấp thực thi, xác định chính xác *tại sao và ở span nào bị chậm* (phát hiện span `retrieval` chiếm 2.501s / 2.663s).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - *Prompt Versioning & Rollback:* Tách biệt vòng đời của prompt khỏi vòng đời triển khai code. Khi phiên bản mới (v2) gây suy giảm chất lượng hoặc tăng token bất ngờ, quản trị viên có thể rollback nhãn `production` về v1 ngay lập tức trên UI mà không cần can thiệp code hay restart container.
  - *Token & Cost Tracking:* Giám sát chi phí thời gian thực theo từng request, phòng ngừa rủi ro cạn ngân sách do prompt injection hoặc lặp câu trả lời vô hạn.
  - *SLO & Error Budget:* Thiết lập cam kết định lượng về chất lượng dịch vụ (99.5% fast & success), giúp đội ngũ cân bằng giữa tốc độ release tính năng mới và độ tin cậy của hệ thống.
- **Điều quan trọng nhất đã học:** Nắm vững quy trình vận hành và quan sát LLMOps chuyên nghiệp: từ việc xây dựng hệ thống telemetry chuẩn mực (không rò rỉ PII), liên kết chặt chẽ ba trụ cột Metrics - Logs - Traces, cho đến điều tra và giải quyết sự cố theo chuỗi bằng chứng không thể chối cãi.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các dịch vụ Vector DB và LLM hiện đang chạy mock cục bộ để phục vụ mục đích lab; trong môi trường sản xuất quy mô lớn cần tích hợp OpenTelemetry collector chuẩn và multi-tenant distributed tracing.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có đúng 3 file text và các ảnh runtime theo hướng dẫn.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

