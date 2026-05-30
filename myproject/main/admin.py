from django.contrib import admin
from .models import (
    Profile,
    CourseCategory,
    Course,
    CourseChapter,
    CourseLesson,
    Enrollment,
    LearningRecord,
    Coupon,
    UserCoupon,
    Promotion,
    Cart,
    CartItem,
    Order,
    OrderItem,
    CouponUsage,
    Payment,
    Refund,
    Favorite,
    Review,
    Notification,
    CourseQuestion,
    CourseAnswer,
    CourseAudit,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username',)
    list_filter = ('role',)


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'price', 'level', 'is_published', 'created_at')
    search_fields = ('title', 'teacher__username', 'category__name')
    list_filter = ('teacher', 'category', 'level', 'is_published')


@admin.register(CourseChapter)
class CourseChapterAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'sort_order', 'created_at')
    search_fields = ('course__title', 'title')
    list_filter = ('course',)


@admin.register(CourseLesson)
class CourseLessonAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'title', 'duration_minutes', 'sort_order', 'is_free_preview', 'created_at')
    search_fields = ('chapter__course__title', 'chapter__title', 'title')
    list_filter = ('chapter__course', 'is_free_preview')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'purchased_at')
    search_fields = ('student__username', 'course__title')
    list_filter = ('purchased_at',)


@admin.register(LearningRecord)
class LearningRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'lesson', 'minutes', 'watched_at')
    search_fields = ('user__username', 'course__title', 'lesson__title')
    list_filter = ('course', 'watched_at')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'discount_type',
        'discount_value',
        'min_spend',
        'start_date',
        'end_date',
        'usage_limit',
        'is_active',
    )
    search_fields = ('code', 'name')
    list_filter = ('discount_type', 'is_active')


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'status', 'received_at', 'used_at')
    search_fields = ('user__username', 'coupon__code')
    list_filter = ('status', 'received_at')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active')
    search_fields = ('name',)
    list_filter = ('discount_type', 'is_active')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'course', 'added_at')
    search_fields = ('cart__user__username', 'course__title')
    list_filter = ('added_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'course',
        'original_price',
        'discount_amount',
        'final_price',
        'status',
        'created_at',
    )
    search_fields = ('user__username', 'course__title')
    list_filter = ('status', 'created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'course', 'price')
    search_fields = ('order__user__username', 'course__title')


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'order', 'discount_amount', 'used_at')
    search_fields = ('user__username', 'coupon__code', 'order__course__title')
    list_filter = ('used_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'method', 'amount', 'status', 'transaction_no', 'paid_at', 'created_at')
    search_fields = ('order__user__username', 'transaction_no')
    list_filter = ('method', 'status', 'created_at')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'amount', 'status', 'created_at', 'processed_at')
    search_fields = ('user__username', 'order__id')
    list_filter = ('status', 'created_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at')
    search_fields = ('user__username', 'course__title')
    list_filter = ('created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating', 'created_at', 'updated_at')
    search_fields = ('user__username', 'course__title', 'comment')
    list_filter = ('rating', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    list_filter = ('is_read', 'created_at')


@admin.register(CourseQuestion)
class CourseQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'lesson', 'title', 'created_at')
    search_fields = ('user__username', 'course__title', 'title', 'content')
    list_filter = ('course', 'created_at')


@admin.register(CourseAnswer)
class CourseAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'created_at')
    search_fields = ('question__title', 'user__username', 'content')
    list_filter = ('created_at',)


@admin.register(CourseAudit)
class CourseAuditAdmin(admin.ModelAdmin):
    list_display = ('course', 'reviewer', 'status', 'created_at', 'reviewed_at')
    search_fields = ('course__title', 'reviewer__username', 'comment')
    list_filter = ('status', 'created_at')