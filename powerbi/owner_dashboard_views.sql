-- =====================================================================
-- 老闆端 Power BI 儀表板 — MySQL 檢視表 (Views)
-- 專案: GGWP (Django app: main)
-- 用途: 平台整體經營視角 — 年度/月度營業額、熱賣/冷門課程、
--       分類/講師營運表現比較、退款與折扣成本總覽
--
-- 依賴: 先執行同資料夾的 teacher_dashboard_views.sql
--       (本檔用到裡面的 vw_course_sales_summary / vw_refund_detail / vw_order_item_discount)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. 平台每日營收 (拉長歷史,不像現有 platform_analytics 頁只看近 30 天)
--    gross_amount = 折扣前售價加總; paid_amount = 實付(真正入帳的營業額)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_platform_daily_revenue AS
SELECT
    DATE(o.created_at)          AS order_date,
    COUNT(DISTINCT o.id)          AS paid_order_count,
    SUM(oi.price)                  AS gross_amount,
    SUM(oi.discount_amount)          AS discount_amount,
    SUM(oi.paid_amount)                AS paid_amount
FROM main_order o
JOIN main_orderitem oi ON oi.order_id = o.id
WHERE o.status = 'paid'
GROUP BY DATE(o.created_at);


-- ---------------------------------------------------------------------
-- 2. 平台每日退款 (跟營收表分開,Power BI 裡用日期表關聯即可對齊)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_platform_daily_refund AS
SELECT
    DATE(r.created_at) AS refund_date,
    COUNT(*)             AS refund_count,
    SUM(r.amount)          AS refund_amount
FROM main_refund r
WHERE r.status IN ('approved', 'completed')
GROUP BY DATE(r.created_at);


-- ---------------------------------------------------------------------
-- 3. 分類營運表現 (堆疊在 vw_course_sales_summary 上面聚合,不用重寫 join)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    COALESCE(category_name, '未分類')      AS category_name,
    COUNT(*)                                 AS course_count,
    SUM(enrollment_count)                      AS total_enrollment,
    SUM(paid_amount)                             AS total_revenue,
    AVG(avg_rating)                                AS avg_rating,
    SUM(refund_count)                                AS refund_count,
    CASE WHEN SUM(enrollment_count) = 0 THEN NULL
         ELSE SUM(refund_count) / SUM(enrollment_count)
    END                                                AS refund_rate
FROM vw_course_sales_summary
GROUP BY COALESCE(category_name, '未分類');


-- ---------------------------------------------------------------------
-- 4. 講師營運表現
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_teacher_performance AS
SELECT
    teacher_id,
    teacher_username,
    COUNT(*)                    AS course_count,
    SUM(enrollment_count)         AS total_enrollment,
    SUM(paid_amount)                AS total_revenue,
    AVG(avg_rating)                   AS avg_rating,
    SUM(refund_count)                   AS refund_count,
    CASE WHEN SUM(enrollment_count) = 0 THEN NULL
         ELSE SUM(refund_count) / SUM(enrollment_count)
    END                                    AS refund_rate
FROM vw_course_sales_summary
GROUP BY teacher_id, teacher_username;


-- ---------------------------------------------------------------------
-- 5. 逐筆訂單明細營業額 (最細顆粒度: 每一筆 OrderItem)
--    「詳細營業額」用這張 — 可以照日期、課程、分類、講師、付款方式
--    任意切,或在 Power BI 拉一張逐筆明細表當鑽研(drill-through)頁
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_revenue_detail AS
SELECT
    oi.id                       AS order_item_id,
    o.id                          AS order_id,
    DATE(o.created_at)             AS order_date,
    o.created_at                     AS order_datetime,
    c.id                                AS course_id,
    c.title                              AS course_title,
    COALESCE(cat.name, '未分類')           AS category_name,
    c.teacher_id                             AS teacher_id,
    tu.username                                AS teacher_username,
    stu.id                                       AS student_id,
    stu.username                                   AS student_username,
    oi.price                                         AS list_price,      -- 折扣前售價
    oi.discount_amount                                 AS discount_amount, -- 促銷+券折扣
    oi.paid_amount                                       AS paid_amount,   -- 實付(真正入帳)
    pay.method                                             AS payment_method,
    cu.coupon_id                                             AS coupon_id,
    coup.code                                                  AS coupon_code
FROM main_orderitem oi
JOIN main_order o ON o.id = oi.order_id
JOIN main_course c ON c.id = oi.course_id
JOIN auth_user tu ON tu.id = c.teacher_id
JOIN auth_user stu ON stu.id = o.user_id
LEFT JOIN main_coursecategory cat ON cat.id = c.category_id
LEFT JOIN main_couponusage cu ON cu.order_id = o.id
LEFT JOIN main_coupon coup ON coup.id = cu.coupon_id
LEFT JOIN (
    -- 一張訂單理論上只有一筆成功付款,用 MIN(id) 取一筆避免重複行
    SELECT p1.order_id, p1.method
    FROM main_payment p1
    WHERE p1.status = 'paid'
      AND p1.id = (
          SELECT MIN(p2.id) FROM main_payment p2
          WHERE p2.order_id = p1.order_id AND p2.status = 'paid'
      )
) pay ON pay.order_id = o.id
WHERE o.status = 'paid';
