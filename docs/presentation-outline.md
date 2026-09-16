# Dàn ý trình bày và demo dự án

## Mạch nội dung

Nhóm trình bày theo hành trình dữ liệu: vấn đề nghiệp vụ → dữ liệu nguồn → mô hình
Kimball → ETL và chất lượng → ML/risk policy → ứng dụng cảnh báo → kết luận.

| Phần | Người trình bày | Thời lượng | Bằng chứng chính |
|---|---|---:|---|
| Mở đầu, yêu cầu nghiệp vụ, kiến trúc | TV1 | 2 phút | README, Bus Matrix |
| Vấn đề dữ liệu và EDA | TV3 | 3 phút | profiling, fraud insights |
| Grain, DateKey/TimeKey, ETL | TV2 | 5 phút | Star Schema, log ETL, SQL validation |
| Model, threshold, risk policy | TV4 | 4 phút | metadata, confusion matrix, scoring |
| API/Streamlit và feedback | TV5 | 4 phút | Alert Queue, feedback form |
| Kết luận và giới hạn | TV1 | 2 phút | KPI nghiệm thu, hướng phát triển |

## Các câu bắt buộc phải giải thích

`FactTransaction` có grain một giao dịch. `FactModelScore` có grain một giao dịch
được chấm bởi một phiên bản model. `FactAlert` có grain một cảnh báo HIGH/CRITICAL.

PaySim không có timestamp thực. `step` được đổi thành `StepDay`, `HourOfDay`,
`DateKey` và `TimeKey`, với ngày 2023-01-01 chỉ là mốc mô phỏng.

ETL sử dụng batch theo chunk, staging, validation/reject, nạp dimension trước fact,
reconciliation và business-key idempotency. Dữ liệu mới trong cùng miền `step` được
nạp bằng cách đổi file đầu vào và chạy lại pipeline; các fact đã tồn tại không được
insert lại.

## Kịch bản demo rút gọn

TV3 chạy test dữ liệu nhỏ. TV2 trình bày SQL validation trên database đã nạp sẵn.
TV4 chạy scoring mẫu hoặc mở output đã tạo trước. TV5 cập nhật phản hồi cho một alert
trong Streamlit. Không chạy full ETL hay full training trong thời gian thuyết trình.

## Số liệu thống nhất

| Chỉ số | Giá trị |
|---|---:|
| Giao dịch | 6.362.620 |
| Fraud | 8.213 |
| Fraud rate | 0,129% |
| Threshold | 0,32 |
| Test Recall/F2 | 99,92% |
| HIGH + CRITICAL | 8.218 |
| Reconciliation | 100% |

Không diễn giải metric PaySim như hiệu năng đã được chứng minh trên ngân hàng thực.
