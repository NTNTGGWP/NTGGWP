-- =====================================================================
-- 講師端 Power BI 儀表板 — MySQL 檢視表 (Views)
-- 專案: GGWP (Django app: main)
-- 用途: 把 Django ORM 的正規化資料表,整理成 Power BI 好接的寬表
--       Power BI Desktop 用「取得資料 > MySQL 資料庫」直接匯入下面這些 view
--       跟接原始表比,好處是: 這裡先把「已知的語意債」(見 CONTEXT.md) 處理掉,
--       Power BI 那邊不用再重算一次分潤/退款/完成率的邏輯
--
-- 執行方式: 用你們專案現有的 DB 連線資訊,在 MySQL client
--          (Workbench / DataGrip / mysql CLI) 執行這份檔案一次即可,
--          之後資料異動,view 會自動反映最新狀態,不用重跑。
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. 收支分潤明細 (真實淨收入用)
--    直接對應 RevenueRecord,已經是「扣掉行銷成本分攤後」的講師實拿金額
--    status='confirmed' 才算數;'reversed' 是退款沖銷掉的,不計入淨收入
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_teacher_revenue_ledger AS
SELECT
    rr.id                    AS revenue_record_id,
    rr.teacher_id             AS teacher_id,
    u.username                AS teacher_username,
    rr.course_id               AS course_id,
    c.title                    AS course_title,
    rr.order_id                AS order_id,
    rr.order_item_id           AS order_item_id,
    rr.gross_amount            AS gross_amount,
    rr.marketing_cost          AS marketing_cost,
    rr.teacher_split_percent   AS teacher_split_percent,
    rr.teacher_amount          AS teacher_amount,
    rr.company_amount          AS company_amount,
    rr.status                  AS status,           -- confirmed / reversed
    rr.created_at              AS created_at,
    rr.reversed_at             AS reversed_at
FROM main_revenuerecord rr
JOIN main_course c ON c.id = rr.course_id
JOIN auth_user u   ON u.id = rr.teacher_id;


-- ---------------------------------------------------------------------
-- 2. 提領紀錄 + 可提領餘額
--    可提領餘額的算法跟 WithdrawalRequest.available_balance() 完全一致:
--    已確認分潤總額 − (待處理+已完成)的提領金額
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_teacher_withdrawals AS
SELECT
    wr.id            AS withdrawal_id,
    wr.teacher_id     AS teacher_id,
    u.username         AS teacher_username,
    wr.amount          AS amount,
    wr.status          AS status,        -- pending / completed / rejected
    wr.requested_at    AS requested_at,
    wr.processed_at    AS processed_at
FROM main_withdrawalrequest wr
JOIN auth_user u ON u.id = wr.teacher_id;

CREATE OR REPLACE VIEW vw_teacher_balance AS
SELECT
    u.id AS teacher_id,
    u.username AS teacher_username,
    COALESCE(confirmed.total, 0) AS confirmed_total,
    COALESCE(reserved.total, 0)  AS reserved_total,
    COALESCE(confirmed.total, 0) - COALESCE(reserved.total, 0) AS available_balance
FROM auth_user u
LEFT JOIN (
    SELECT teacher_id, SUM(teacher_amount) AS total
    FROM main_revenuerecord
    WHERE status = 'confirmed'
    GROUP BY teacher_id
) confirmed ON confirmed.teacher_id = u.id
LEFT JOIN (
    SELECT teacher_id, SUM(amount) AS total
    FROM main_withdrawalrequest
    WHERE status IN ('pending', 'completed')
    GROUP BY teacher_id
) reserved ON reserved.teacher_id = u.id;


-- ---------------------------------------------------------------------
-- 3. 課程銷售總覽 (每課一列)
--    注意: Order.course 在多課程訂單(購物車)裡是 NULL (見 CONTEXT.md 語意債),
--    所以銷售/營收一律用 OrderItem 反推,不要用 Order.course
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_course_sales_summary AS
SELECT
    c.id                       AS course_id,
    c.title                    AS course_title,
    c.teacher_id                AS teacher_id,
    u.username                  AS teacher_username,
    cat.name                    AS category_name,
    c.price                     AS list_price,
    c.is_published               AS is_published,
    c.created_at                 AS course_created_at,
    COALESCE(enr.enrollment_count, 0)   AS enrollment_count,
    COALESCE(sales.paid_item_count, 0)  AS paid_item_count,
    COALESCE(sales.gross_amount, 0)     AS gross_amount,      -- OrderItem.price 加總 (促銷/券前)
    COALESCE(sales.paid_amount, 0)      AS paid_amount,       -- OrderItem.paid_amount 加總 (實付)
    COALESCE(sales.discount_amount, 0)  AS discount_amount,   -- 促銷+券折扣加總
    COALESCE(rf.refund_count, 0)        AS refund_count,
    COALESCE(rf.refund_amount, 0)       AS refund_amount,
    COALESCE(rev.review_count, 0)       AS review_count,
    rev.avg_rating                      AS avg_rating,
    COALESCE(fav.favorite_count, 0)     AS favorite_count
FROM main_course c
JOIN auth_user u ON u.id = c.teacher_id
LEFT JOIN main_coursecategory cat ON cat.id = c.category_id
LEFT JOIN (
    SELECT course_id, COUNT(*) AS enrollment_count
    FROM main_enrollment
    GROUP BY course_id
) enr ON enr.course_id = c.id
LEFT JOIN (
    SELECT
        oi.course_id,
        COUNT(*)                AS paid_item_count,
        SUM(oi.price)            AS gross_amount,
        SUM(oi.paid_amount)      AS paid_amount,
        SUM(oi.discount_amount)  AS discount_amount
    FROM main_orderitem oi
    JOIN main_order o ON o.id = oi.order_id
    WHERE o.status = 'paid'
    GROUP BY oi.course_id
) sales ON sales.course_id = c.id
LEFT JOIN (
    -- 一筆退款可能對應到多課程訂單,這裡用 DISTINCT order_id+course_id 避免同一課被重複算
    SELECT
        oi.course_id,
        COUNT(DISTINCT r.id)  AS refund_count,
        SUM(r.amount)          AS refund_amount
    FROM main_refund r
    JOIN main_orderitem oi ON oi.order_id = r.order_id
    WHERE r.status IN ('approved', 'completed')
    GROUP BY oi.course_id
) rf ON rf.course_id = c.id
LEFT JOIN (
    SELECT course_id, COUNT(*) AS review_count, AVG(rating) AS avg_rating
    FROM main_review
    GROUP BY course_id
) rev ON rev.course_id = c.id
LEFT JOIN (
    SELECT course_id, COUNT(*) AS favorite_count
    FROM main_favorite
    GROUP BY course_id
) fav ON fav.course_id = c.id;


-- ---------------------------------------------------------------------
-- 4. 退款明細 (逐筆,給退款原因分析用)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_refund_detail AS
SELECT DISTINCT
    r.id            AS refund_id,
    r.order_id       AS order_id,
    oi.course_id      AS course_id,
    c.title            AS course_title,
    c.teacher_id       AS teacher_id,
    r.user_id          AS student_id,
    stu.username        AS student_username,
    r.amount            AS amount,
    r.reason            AS reason,
    r.status            AS status,
    r.created_at         AS created_at,
    r.processed_at       AS processed_at
FROM main_refund r
JOIN main_orderitem oi ON oi.order_id = r.order_id
JOIN main_course c ON c.id = oi.course_id
JOIN auth_user stu ON stu.id = r.user_id;


-- ---------------------------------------------------------------------
-- 5. 訂單明細折扣 (優惠券/促銷對銷量的影響用)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_order_item_discount AS
SELECT
    oi.id             AS order_item_id,
    oi.order_id        AS order_id,
    oi.course_id        AS course_id,
    c.title              AS course_title,
    c.teacher_id         AS teacher_id,
    o.status              AS order_status,
    o.created_at           AS order_created_at,
    oi.price                AS price,
    oi.discount_amount       AS discount_amount,
    oi.paid_amount           AS paid_amount,
    cu.coupon_id              AS coupon_id,
    coup.code                  AS coupon_code
FROM main_orderitem oi
JOIN main_order o ON o.id = oi.order_id
JOIN main_course c ON c.id = oi.course_id
LEFT JOIN main_couponusage cu ON cu.order_id = o.id
LEFT JOIN main_coupon coup ON coup.id = cu.coupon_id;


-- ---------------------------------------------------------------------
-- 6. 單元完成率 / 棄看熱點 (每單元一列)
--    watched_seconds / duration 就是 LessonProgress.percent() 的邏輯
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_lesson_completion AS
SELECT
    l.id                 AS lesson_id,
    l.title               AS lesson_title,
    l.sort_order           AS lesson_sort_order,
    ch.id                   AS chapter_id,
    ch.title                 AS chapter_title,
    co.id                     AS course_id,
    co.title                   AS course_title,
    co.teacher_id               AS teacher_id,
    l.duration_minutes           AS duration_minutes,
    COUNT(lp.id)                  AS viewers_count,
    SUM(CASE WHEN lp.is_completed THEN 1 ELSE 0 END) AS completed_count,
    CASE WHEN COUNT(lp.id) = 0 THEN NULL
         ELSE SUM(CASE WHEN lp.is_completed THEN 1 ELSE 0 END) / COUNT(lp.id)
    END                             AS completion_rate,
    AVG(
        CASE WHEN lp.duration > 0 THEN lp.watched_seconds / lp.duration * 100 ELSE NULL END
    )                               AS avg_watch_percent
FROM main_courselesson l
JOIN main_coursechapter ch ON ch.id = l.chapter_id
JOIN main_course co ON co.id = ch.course_id
LEFT JOIN main_lessonprogress lp ON lp.lesson_id = l.id
GROUP BY
    l.id, l.title, l.sort_order, ch.id, ch.title,
    co.id, co.title, co.teacher_id, l.duration_minutes;


-- ---------------------------------------------------------------------
-- 7. 學生互動 (評價 + 問答,每課一列)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_course_engagement AS
SELECT
    co.id                          AS course_id,
    co.title                        AS course_title,
    co.teacher_id                    AS teacher_id,
    COALESCE(q.question_count, 0)     AS question_count,
    COALESCE(q.unanswered_count, 0)    AS unanswered_count,
    q.avg_response_minutes              AS avg_response_minutes
FROM main_course co
LEFT JOIN (
    SELECT
        cq.course_id,
        COUNT(*) AS question_count,
        SUM(CASE WHEN first_ans.first_answered_at IS NULL THEN 1 ELSE 0 END) AS unanswered_count,
        AVG(
            CASE WHEN first_ans.first_answered_at IS NOT NULL
                 THEN TIMESTAMPDIFF(MINUTE, cq.created_at, first_ans.first_answered_at)
                 ELSE NULL END
        ) AS avg_response_minutes
    FROM main_coursequestion cq
    LEFT JOIN (
        SELECT question_id, MIN(created_at) AS first_answered_at
        FROM main_courseanswer
        GROUP BY question_id
    ) first_ans ON first_ans.question_id = cq.id
    GROUP BY cq.course_id
) q ON q.course_id = co.id;


-- ---------------------------------------------------------------------
-- 8. 評價明細 (逐筆,給評分趨勢用 — Power BI 自己的日期表可以直接抓 created_at 分月)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_review_detail AS
SELECT
    rv.id           AS review_id,
    rv.course_id      AS course_id,
    c.title            AS course_title,
    c.teacher_id        AS teacher_id,
    rv.user_id           AS student_id,
    rv.rating              AS rating,
    rv.created_at            AS created_at
FROM main_review rv
JOIN main_course c ON c.id = rv.course_id;
