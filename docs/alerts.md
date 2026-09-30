# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Primary SLO `fast_successful_requests` (latency P95 của `response_sent.latency_ms` <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng bị trễ phản hồi, thời gian chờ câu trả lời vượt ngưỡng cam kết (> 3s).
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở panel Latency trên Dashboard để kiểm tra P50/P95/P99 và TTFT nhằm xác định thời điểm bắt đầu tăng đột biến.
  2. **Logs:** Lọc `data/logs.jsonl` tìm các event `response_sent` có `latency_ms > 3000` trong khung giờ đó, trích xuất `correlation_id` đại diện.
  3. **Traces:** Mở trace cùng `correlation_id` trên Langfuse, so sánh thời gian thực thi của span `retrieval` và observation `generation` để xác định nghẽn tại bước nào (ví dụ sự cố RAG slow).
- Mitigation tạm thời: Tắt incident `rag_slow` qua `/incidents/rag_slow/disable`, cấu hình giảm timeout retrieval hoặc kích hoạt cơ chế fallback context cache.
- Owner: `student-2A202602633`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `error_rate_pct_max <= 2%` và `retrieval_success_rate_pct_min >= 90%`
- Điều kiện và thời gian duy trì: `error_rate > 2%` hoặc `retrieval_success_rate < 90%` duy trì trong 3 phút
- Ảnh hưởng tới người dùng: Yêu cầu bị lỗi (HTTP 500), người dùng không nhận được câu trả lời từ hệ thống.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Kiểm tra panel Errors và Retrieval Success trên Dashboard để xác định tỉ lệ lỗi và thành phần gây lỗi.
  2. **Logs:** Lọc `data/logs.jsonl` tìm các log `request_failed`, xem trường `error_type`, `detail` và lấy `correlation_id` tương ứng.
  3. **Traces:** Tìm trace có `correlation_id` trên Langfuse, kiểm tra span bị đánh dấu `ERROR` (như span `retrieval` bị timeout/RuntimeError).
- Mitigation tạm thời: Tắt incident `tool_fail` qua `/incidents/tool_fail/disable`, khởi động lại service phụ thuộc hoặc kích hoạt chế độ trả lời fallback khi retrieval thất bại.
- Owner: `student-2A202602633`

## Alert 3

- Tên: `CostBurnSpike`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `daily_cost_usd_max <= 2.5$` và độ dài token
- Điều kiện và thời gian duy trì: Chi phí ước tính tích lũy tăng nhanh vượt ngưỡng bảo vệ (`daily_cost_usd > $2.5` hoặc output tokens tăng gấp 4 lần) duy trì trong 5 phút
- Ảnh hưởng tới người dùng: Có thể bị giới hạn hạn ngạch (rate limit/quota), nguy cơ cạn kiệt ngân sách vận hành mô hình.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở panel Cost và Tokens trên Dashboard để xác định lượng token in/out và tốc độ tăng chi phí theo thời gian.
  2. **Logs:** Lọc log `response_sent` có `tokens_out` hoặc `cost_usd` cao bất thường, lấy `correlation_id` và `prompt_version`.
  3. **Traces:** Mở trace trên Langfuse, kiểm tra observation `generation` để xem số token in/out, cost chi tiết và prompt template đang kích hoạt.
- Mitigation tạm thời: Rollback prompt về version ổn định trước đó (nếu do prompt v2 sinh quá dài), tắt incident `cost_spike` qua `/incidents/cost_spike/disable`, áp đặt `max_tokens` chặt chẽ hơn trong cấu hình gọi LLM.
- Owner: `student-2A202602633`
