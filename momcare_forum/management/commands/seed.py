import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from momcare_forum.models import (
    AdminActivityLog,
    Category,
    Comment,
    Notification,
    OTPToken,
    Post,
    PostVerification,
    Report,
    SystemSettings,
    UserProfile,
)


class Command(BaseCommand):
    help = 'Seed dữ liệu mẫu đầy đủ cho hệ thống MomCare Forum'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Xóa dữ liệu forum hiện có trước khi tạo dữ liệu mẫu.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(20260402)

        self.stdout.write(self.style.SUCCESS('=' * 72))
        self.stdout.write(self.style.SUCCESS('MOMCARE FORUM - FULL SAMPLE SEED'))
        self.stdout.write(self.style.SUCCESS('=' * 72))

        if options['reset']:
            self._reset_forum_data()

        categories = self._seed_categories()
        users = self._seed_users()

        posts = self._seed_posts(users, categories)
        comments = self._seed_comments(users, posts, rng)

        self._seed_likes(users, posts, comments, rng)
        self._seed_reports(users, posts, comments, rng)
        self._seed_notifications(users, posts, comments, rng)
        self._seed_system_settings(users)
        self._seed_otp_tokens()
        self._seed_admin_logs(users, posts, comments)

        self._print_summary(users)

    def _reset_forum_data(self):
        self.stdout.write('\n[0] Reset dữ liệu forum...')
        AdminActivityLog.objects.all().delete()
        Notification.objects.all().delete()
        Report.objects.all().delete()
        OTPToken.objects.all().delete()
        Comment.objects.all().delete()
        PostVerification.objects.all().delete()
        Post.objects.all().delete()
        UserProfile.objects.all().delete()
        Category.objects.all().delete()

        demo_usernames = [
            'admin_momcare',
            'mod_hoa',
            'bac_si_linh',
            'bac_si_minh',
            'me_an',
            'me_bich',
            'me_cuong',
            'ba_bau_lan',
            'user_spam_01',
        ]
        User.objects.filter(username__in=demo_usernames).delete()
        self.stdout.write(self.style.SUCCESS('  - Đã xóa dữ liệu forum cũ.'))

    def _seed_categories(self):
        self.stdout.write('\n[1] Tạo danh mục...')
        categories_data = [
            ('Mang thai', 'pink', 'Theo dõi thai kỳ, khám thai, dấu hiệu cần chú ý.'),
            ('Sau sinh', 'blue', 'Phục hồi thể chất và tinh thần của mẹ sau sinh.'),
            ('Sơ sinh 0-3 tháng', 'green', 'Ăn ngủ, vệ sinh, theo dõi chỉ số bé sơ sinh.'),
            ('Bé 4-12 tháng', 'orange', 'Ăn dặm, vận động và mốc phát triển của bé.'),
            ('Dinh dưỡng mẹ và bé', 'purple', 'Thực đơn và vi chất cho mẹ bầu, mẹ sau sinh, trẻ nhỏ.'),
            ('Sức khỏe nhi khoa', 'teal', 'Phòng bệnh, xử lý triệu chứng thường gặp ở trẻ.'),
            ('Nuôi con bằng sữa mẹ', 'pink', 'Kinh nghiệm và vấn đề thường gặp khi cho con bú.'),
            ('Sức khỏe tinh thần', 'blue', 'Stress, lo âu, trầm cảm sau sinh và hỗ trợ tâm lý.'),
        ]

        categories = {}
        for name, color_dot, description in categories_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'color_dot': color_dot,
                    'description': description,
                },
            )
            if not created:
                category.color_dot = color_dot
                category.description = description
                category.save(update_fields=['color_dot', 'description'])
            categories[name] = category
            status = 'TẠO' if created else 'CẬP NHẬT'
            self.stdout.write(f'  - {status}: {name}')

        return categories

    def _seed_users(self):
        self.stdout.write('\n[2] Tạo tài khoản và hồ sơ...')
        users_data = [
            {
                'username': 'admin_momcare',
                'email': 'admin@momcare.vn',
                'password': 'Admin123!@#',
                'first_name': 'Admin',
                'last_name': 'MomCare',
                'is_staff': True,
                'is_superuser': True,
                'user_type': 'admin',
                'bio': 'Tài khoản quản trị hệ thống MomCare.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
            {
                'username': 'mod_hoa',
                'email': 'moderator.hoa@momcare.vn',
                'password': 'ModHoa123!@#',
                'first_name': 'Hoa',
                'last_name': 'Lê',
                'is_staff': True,
                'is_superuser': False,
                'user_type': 'admin',
                'bio': 'Điều phối viên nội dung và xử lý báo cáo cộng đồng.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
            {
                'username': 'bac_si_linh',
                'email': 'bacsilinh@momcare.vn',
                'password': 'BacSi123!@#',
                'first_name': 'Linh',
                'last_name': 'Trần',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'doctor',
                'bio': 'Bác sĩ Nhi khoa, 10 năm kinh nghiệm chăm sóc trẻ sơ sinh.',
                'is_verified_doctor': True,
                'doctor_title': 'BS.CKII Nhi khoa',
            },
            {
                'username': 'bac_si_minh',
                'email': 'bacsiminh@momcare.vn',
                'password': 'BacSiMinh123!@#',
                'first_name': 'Minh',
                'last_name': 'Phạm',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'doctor',
                'bio': 'Bác sĩ Sản khoa, tư vấn thai kỳ nguy cơ thấp và trung bình.',
                'is_verified_doctor': True,
                'doctor_title': 'BS.CKI Sản phụ khoa',
            },
            {
                'username': 'me_an',
                'email': 'me.an@momcare.vn',
                'password': 'MeAn123!@#',
                'first_name': 'An',
                'last_name': 'Nguyễn',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'user',
                'bio': 'Mẹ bỉm 7 tháng, thích chia sẻ kinh nghiệm ăn dặm.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
            {
                'username': 'me_bich',
                'email': 'me.bich@momcare.vn',
                'password': 'MeBich123!@#',
                'first_name': 'Bích',
                'last_name': 'Đỗ',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'user',
                'bio': 'Mẹ sinh mổ, quan tâm phục hồi sau sinh và nuôi con bằng sữa mẹ.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
            {
                'username': 'me_cuong',
                'email': 'me.cuong@momcare.vn',
                'password': 'MeCuong123!@#',
                'first_name': 'Cường',
                'last_name': 'Vũ',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'user',
                'bio': 'Mẹ có bé sơ sinh 1 tháng tuổi, đang học chăm bé đúng cách.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
            {
                'username': 'ba_bau_lan',
                'email': 'bau.lan@momcare.vn',
                'password': 'BaBauLan123!@#',
                'first_name': 'Lan',
                'last_name': 'Phan',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'user',
                'bio': 'Mẹ bầu tuần 30, quan tâm dinh dưỡng thai kỳ và chuyển dạ.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
            {
                'username': 'user_spam_01',
                'email': 'spam01@momcare.vn',
                'password': 'SpamUser123!@#',
                'first_name': 'Tài khoản',
                'last_name': 'Spam',
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'user',
                'bio': 'Tài khoản mẫu cho kịch bản vi phạm.',
                'is_verified_doctor': False,
                'doctor_title': '',
            },
        ]

        users = {}
        for item in users_data:
            user, created = User.objects.get_or_create(
                username=item['username'],
                defaults={
                    'email': item['email'],
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'is_staff': item['is_staff'],
                    'is_superuser': item['is_superuser'],
                },
            )

            user.email = item['email']
            user.first_name = item['first_name']
            user.last_name = item['last_name']
            user.is_staff = item['is_staff']
            user.is_superuser = item['is_superuser']
            user.set_password(item['password'])
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.user_type = item['user_type']
            profile.bio = item['bio']
            profile.is_verified_doctor = item['is_verified_doctor']
            profile.doctor_title = item.get('doctor_title', '')
            profile.save()

            users[item['username']] = user
            status = 'TẠO' if created else 'CẬP NHẬT'
            self.stdout.write(f"  - {status}: {item['username']} ({item['user_type']})")

        return users

    def _seed_posts(self, users, categories):
        self.stdout.write('\n[4] Tạo bài viết mẫu...')
        now = timezone.now()
        post_blueprints = [
            ('Mẹ bầu tuần 32 nên đi bộ bao nhiêu phút mỗi ngày?', 'Mình đang ở tuần 32, bác sĩ dặn nên vận động nhẹ mỗi ngày để ngủ ngon và đỡ phù chân. Có mẹ nào duy trì đi bộ đều không, mỗi ngày đi bao lâu thì phù hợp?', 'Mang thai', 'ba_bau_lan', 'public', False),
            ('Dấu hiệu chuyển dạ giả và thật khác nhau thế nào?', 'Mấy hôm nay mình bị gò cứng bụng theo cơn nhưng chưa đều. Mình hơi lo không biết đã cần vào viện chưa. Mong được chia sẻ kinh nghiệm phân biệt cơn gò thật và giả.', 'Mang thai', 'ba_bau_lan', 'anonymous', False),
            ('Lịch khám thai 3 tháng cuối mình đang theo', 'Mình chia sẻ lại lịch khám thai 3 tháng cuối gồm siêu âm, theo dõi tim thai, xét nghiệm máu cơ bản để mẹ nào mới mang thai lần đầu tiện tham khảo.', 'Mang thai', 'me_bich', 'public', True),
            ('Kinh nghiệm giảm đau vết mổ sau sinh 1 tuần đầu', 'Mẹ nào sinh mổ như mình chắc sẽ thấy 3 ngày đầu rất khó vận động. Mình tổng hợp vài cách bác sĩ hướng dẫn để đỡ đau, đi lại sớm và hạn chế dính ruột.', 'Sau sinh', 'me_bich', 'public', False),
            ('Sau sinh hay khóc và mất ngủ, mình nên làm gì?', 'Mình sinh bé được 5 tuần, gần đây hay cáu gắt và có lúc buồn vô cớ. Mình sợ đây là dấu hiệu trầm cảm sau sinh. Có ai từng trải qua và vượt qua được không?', 'Sức khỏe tinh thần', 'me_an', 'anonymous', False),
            ('Bé sơ sinh ngủ ngày cày đêm có bình thường không?', 'Bé nhà mình 20 ngày tuổi ban ngày ngủ li bì nhưng tối thức liên tục. Mình muốn hỏi cách chỉnh nếp sinh hoạt dần dần mà không gây stress cho bé.', 'Sơ sinh 0-3 tháng', 'me_cuong', 'public', False),
            ('Cách vệ sinh rốn cho bé 1 tuần tuổi', 'Mình được hướng dẫn vệ sinh rốn bằng gạc vô khuẩn và nước muối sinh lý. Mình ghi chi tiết từng bước để mẹ mới có thể làm đúng và yên tâm hơn.', 'Sơ sinh 0-3 tháng', 'me_cuong', 'public', True),
            ('Lịch bú đêm của bé 2 tháng tuổi', 'Bé nhà mình bú cách 3 tiếng ban ngày nhưng đêm lại đòi bú dày hơn. Không biết có nên đánh thức bé bú đúng cữ hay để bé tự điều chỉnh.', 'Sơ sinh 0-3 tháng', 'me_an', 'public', False),
            ('Bé 6 tháng biếng ăn tuần đầu ăn dặm', 'Mình bắt đầu ăn dặm kiểu truyền thống nhưng bé ăn rất ít và hay quay mặt đi. Mình nên đổi kết cấu hay đổi khung giờ ăn trước?', 'Bé 4-12 tháng', 'me_an', 'public', False),
            ('Gợi ý thực đơn ăn dặm 7 ngày cho bé 7 tháng', 'Mình chia sẻ thực đơn 7 ngày gồm tinh bột, đạm, rau, chất béo theo tỉ lệ đơn giản để mẹ mới bắt đầu dễ theo dõi và thay đổi linh hoạt.', 'Bé 4-12 tháng', 'me_bich', 'public', True),
            ('Các dấu hiệu dị ứng đạm sữa bò ở trẻ nhỏ', 'Bé có biểu hiện nổi mẩn quanh miệng và đi phân lỏng sau khi đổi sữa công thức. Mình tổng hợp các dấu hiệu cảnh báo để mẹ tham khảo và đi khám sớm.', 'Sức khỏe nhi khoa', 'bac_si_linh', 'public', True),
            ('Khi nào cần đưa bé sốt đi cấp cứu ngay?', 'Không phải cơn sốt nào cũng nguy hiểm, nhưng có một số dấu hiệu đi kèm cần đi viện ngay như lừ đừ, co giật, tím tái hoặc bỏ bú hoàn toàn.', 'Sức khỏe nhi khoa', 'bac_si_linh', 'public', True),
            ('Bảng tiêm chủng cơ bản cho trẻ dưới 1 tuổi', 'Mình soạn một bảng mốc tiêm cơ bản từ sơ sinh đến 12 tháng để phụ huynh dễ theo dõi, tránh bỏ sót mũi quan trọng.', 'Sức khỏe nhi khoa', 'bac_si_minh', 'public', True),
            ('Mẹ cho con bú cần uống bao nhiêu nước mỗi ngày?', 'Nhiều mẹ sợ uống nhiều nước sẽ phù, nhưng thực tế thiếu nước lại dễ giảm tiết sữa. Mình chia sẻ cách chia lượng nước theo khung giờ.', 'Nuôi con bằng sữa mẹ', 'bac_si_minh', 'public', True),
            ('Mẹ sau sinh nên bổ sung sắt trong bao lâu?', 'Tùy tình trạng thiếu máu và chế độ ăn, nhiều mẹ vẫn cần bổ sung sắt thêm 1-3 tháng sau sinh. Nên tái khám để điều chỉnh liều phù hợp.', 'Dinh dưỡng mẹ và bé', 'bac_si_linh', 'public', True),
            ('Thực đơn 1 ngày cho mẹ sau sinh đủ sữa', 'Mình thử thực đơn gồm 3 bữa chính và 2 bữa phụ trong 2 tuần, thấy sữa về đều hơn và không còn quá đói vào buổi tối.', 'Dinh dưỡng mẹ và bé', 'me_bich', 'public', False),
            ('Cảnh báo: thuốc giảm cân sau sinh bán online', 'Có nhiều quảng cáo giảm cân sau sinh rất nhanh nhưng không rõ thành phần. Nếu đang cho con bú thì tuyệt đối không dùng tùy tiện.', 'Sau sinh', 'bac_si_minh', 'public', True),
            ('Mình lo bị mất sữa sau khi quay lại làm việc', 'Mình sắp đi làm lại, bé mới 5 tháng. Có mẹ nào duy trì được sữa mẹ khi đi làm full-time thì cho mình xin kinh nghiệm nhé.', 'Nuôi con bằng sữa mẹ', 'me_an', 'anonymous', False),
        ]

        reason_cycle = ['accurate', 'safe', 'expert', 'confirmed', 'reference', 'nutrition', 'useful']
        posts = []

        for idx, (title, content, cat_name, username, privacy, verified) in enumerate(post_blueprints):
            post, created = Post.objects.get_or_create(
                title=title,
                author=users[username],
                defaults={
                    'content': content,
                    'category': categories[cat_name],
                    'privacy': privacy,
                },
            )
            if not created:
                post.content = content
                post.category = categories[cat_name]
                post.privacy = privacy

            post.is_hidden = False
            post.save()

            created_at = now - timedelta(days=18 - idx, hours=(idx * 3) % 24)
            Post.objects.filter(pk=post.pk).update(created_at=created_at, updated_at=created_at + timedelta(hours=2))

            if verified:
                doctor_primary = users['bac_si_linh'] if idx % 2 == 0 else users['bac_si_minh']
                reasons = [
                    reason_cycle[idx % len(reason_cycle)],
                    reason_cycle[(idx + 2) % len(reason_cycle)],
                ]

                PostVerification.objects.update_or_create(
                    post=post,
                    doctor=doctor_primary,
                    defaults={
                        'verification_reasons': ','.join(reasons),
                        'verification_note': 'Đã rà soát nội dung và xác nhận bài viết phù hợp với khuyến nghị y khoa.',
                        'verified_at': created_at + timedelta(hours=8),
                    },
                )

                # Add second-doctor review for some posts to test multi-doctor moderation popup.
                if idx % 3 == 0:
                    doctor_secondary = users['bac_si_minh'] if doctor_primary == users['bac_si_linh'] else users['bac_si_linh']
                    PostVerification.objects.update_or_create(
                        post=post,
                        doctor=doctor_secondary,
                        defaults={
                            'verification_reasons': ','.join([reason_cycle[(idx + 1) % len(reason_cycle)], 'expert']),
                            'verification_note': 'Đồng thuận với đánh giá trước đó, bổ sung ghi chú chuyên môn.',
                            'verified_at': created_at + timedelta(hours=12),
                        },
                    )
            else:
                PostVerification.objects.filter(post=post).delete()

            post.refresh_verification_status(save=True)

            posts.append(post)
            status = 'TẠO' if created else 'CẬP NHẬT'
            self.stdout.write(f'  - {status}: {title[:62]}')

        return posts

    def _seed_comments(self, users, posts, rng):
        self.stdout.write('\n[5] Tạo bình luận mẫu...')
        comments = []
        now = timezone.now()
        comment_pool = [
            ('bac_si_linh', 'Bạn mô tả rất rõ, mình bổ sung thêm là nên theo dõi nhiệt độ và nhịp thở của bé 2 lần mỗi ngày.'),
            ('bac_si_minh', 'Thông tin hữu ích. Nếu có dấu hiệu đau tăng hoặc sốt, bạn nên tái khám sớm thay vì tự dùng thuốc.'),
            ('me_an', 'Mình đã thử cách này 1 tuần và thấy bé hợp tác hơn hẳn, cảm ơn bạn đã chia sẻ.'),
            ('me_bich', 'Nhà mình cũng gặp đúng tình trạng này, đổi khung giờ ăn sang buổi sáng thì cải thiện hơn.'),
            ('me_cuong', 'Mẹ nào có thêm checklist theo dõi mỗi ngày thì chia sẻ giúp mình với nhé.'),
            ('ba_bau_lan', 'Đọc xong thấy yên tâm hơn nhiều, cảm ơn bác sĩ và các mẹ trong nhóm.'),
            ('mod_hoa', 'Bài viết rất có ích cho cộng đồng. Mọi người lưu ý chỉ tham khảo và đi khám khi cần.'),
        ]

        for idx, post in enumerate(posts):
            n_comments = 1 + (idx % 3)
            selected = rng.sample(comment_pool, k=n_comments)
            for offset, (username, content) in enumerate(selected):
                comment, created = Comment.objects.get_or_create(
                    post=post,
                    author=users[username],
                    content=content,
                )

                verified = users[username].profile.user_type == 'doctor'
                comment.verified_by_expert = verified
                comment.verified_by = users[username] if verified else None
                comment.verified_at = (post.created_at + timedelta(hours=6 + offset)) if verified else None
                comment.is_hidden = False
                comment.report_count = 0
                comment.save()

                created_at = post.created_at + timedelta(hours=4 + offset)
                Comment.objects.filter(pk=comment.pk).update(created_at=created_at, updated_at=created_at + timedelta(minutes=15))
                comments.append(comment)
                state = 'TẠO' if created else 'CẬP NHẬT'
                self.stdout.write(f'  - {state}: Cmt #{comment.pk} cho bài #{post.pk}')

        # Kịch bản comment vi phạm để test moderation
        bad_post = posts[-1]
        bad_comment, _ = Comment.objects.get_or_create(
            post=bad_post,
            author=users['user_spam_01'],
            content='Inbox mình để mua combo thuốc giảm cân sau sinh, cam kết giảm 7kg trong 10 ngày.',
        )
        bad_comment.report_count = 3
        bad_comment.is_hidden = True
        bad_comment.save(update_fields=['report_count', 'is_hidden'])
        comments.append(bad_comment)
        self.stdout.write('  - TẠO: Bình luận vi phạm mẫu để kiểm thử moderation')

        return comments

    def _seed_likes(self, users, posts, comments, rng):
        self.stdout.write('\n[6] Tạo lượt thích...')
        all_users = list(users.values())

        for post in posts:
            like_count = rng.randint(2, min(6, len(all_users)))
            likers = rng.sample(all_users, like_count)
            post.likes.set(likers)

        for comment in comments:
            like_count = rng.randint(0, 3)
            if like_count == 0:
                comment.likes.clear()
                continue
            likers = rng.sample(all_users, like_count)
            comment.likes.set(likers)

        self.stdout.write(self.style.SUCCESS('  - Đã tạo like cho bài viết và bình luận.'))

    def _seed_reports(self, users, posts, comments, rng):
        self.stdout.write('\n[7] Tạo báo cáo vi phạm...')
        report_types = ['spam', 'false', 'offensive', 'fake_news', 'other']
        reporters = [users['me_an'], users['me_bich'], users['me_cuong'], users['ba_bau_lan']]

        target_posts = [posts[1], posts[4], posts[-1]]
        for idx, post in enumerate(target_posts):
            report, _ = Report.objects.get_or_create(
                reporter=reporters[idx % len(reporters)],
                post=post,
                report_type=report_types[idx],
                defaults={
                    'reason': 'Nội dung cần được đội ngũ kiểm duyệt xem lại.',
                },
            )
            processed = idx != 2
            report.reason = report.reason or 'Nội dung cần được đội ngũ kiểm duyệt xem lại.'
            report.is_processed = processed
            report.processed_by = users['mod_hoa'] if processed else None
            report.processed_at = timezone.now() - timedelta(days=idx + 1) if processed else None
            report.save()

            post.report_count = Report.objects.filter(post=post).count()
            post.is_hidden = post.report_count >= 3
            post.save(update_fields=['report_count', 'is_hidden'])

        # Keep report dataset aligned with current product flow (report posts only).
        target_comment = comments[-1]
        target_comment.report_count = 0
        target_comment.is_hidden = True
        target_comment.save(update_fields=['report_count', 'is_hidden'])

        self.stdout.write(f'  - Tổng số báo cáo: {Report.objects.count()}')

    def _seed_notifications(self, users, posts, comments, rng):
        self.stdout.write('\n[8] Tạo thông báo...')
        Notification.objects.filter(recipient__username__in=users.keys()).delete()

        notifications = [
            {
                'recipient': users['me_cuong'],
                'notification_type': 'comment',
                'title': 'Bạn có bình luận mới',
                'message': 'Bài viết của bạn vừa nhận được bình luận từ bác sĩ.',
                'post': posts[5],
                'comment': comments[0],
            },
            {
                'recipient': users['me_bich'],
                'notification_type': 'verified',
                'title': 'Bài viết đã được kiểm duyệt',
                'message': 'Bài viết của bạn đã được chuyên gia xác nhận thông tin.',
                'post': posts[2],
                'comment': None,
            },
            {
                'recipient': users['me_an'],
                'notification_type': 'report_processed',
                'title': 'Báo cáo của bạn đã được xử lý',
                'message': 'Cảm ơn bạn đã báo cáo. Chúng tôi đã xử lý nội dung vi phạm.',
                'post': posts[-1],
                'comment': None,
            },
            {
                'recipient': users['ba_bau_lan'],
                'notification_type': 'system',
                'title': 'Nhắc lịch khám thai định kỳ',
                'message': 'Bạn nên tái khám trong tuần này theo lịch thai kỳ quý 3.',
                'post': None,
                'comment': None,
            },
        ]

        now = timezone.now()
        for idx, item in enumerate(notifications):
            notification = Notification.objects.create(**item)
            created_at = now - timedelta(hours=8 - idx)
            Notification.objects.filter(pk=notification.pk).update(created_at=created_at)
            if idx % 2 == 0:
                notification.is_read = True
                notification.read_at = created_at + timedelta(minutes=30)
                notification.save(update_fields=['is_read', 'read_at'])

        self.stdout.write(f'  - Tổng số thông báo: {Notification.objects.count()}')

    def _seed_system_settings(self, users):
        self.stdout.write('\n[9] Thiết lập cấu hình hệ thống...')
        admin = users['admin_momcare']
        settings_data = {
            'max_posts_per_day': ('5', 'Giới hạn số bài viết mỗi tài khoản mỗi ngày.'),
            'max_comments_per_day': ('30', 'Giới hạn số bình luận mỗi tài khoản mỗi ngày.'),
            'report_threshold': ('3', 'Tự động ẩn khi nội dung đạt ngưỡng báo cáo.'),
            'email_notifications': ('true', 'Gửi email với thông báo quan trọng.'),
            'moderation_required': ('false', 'Không bắt buộc duyệt trước với bài viết thường.'),
            'auto_ban_threshold': ('7', 'Tự động cấm tạm thời khi vượt ngưỡng báo cáo.'),
            'maintenance_mode': ('false', 'Chế độ bảo trì hệ thống.'),
            'site_announcement': ('Chào mừng bạn đến cộng đồng MomCare.', 'Thông báo hiển thị đầu trang.'),
        }

        for key, (value, description) in settings_data.items():
            obj, _ = SystemSettings.objects.get_or_create(key=key)
            obj.value = value
            obj.description = description
            obj.updated_by = admin
            obj.save()

        self.stdout.write(f'  - Tổng số setting: {SystemSettings.objects.count()}')

    def _seed_otp_tokens(self):
        self.stdout.write('\n[10] Tạo OTP mẫu...')
        OTPToken.objects.all().delete()
        now = timezone.now()

        OTPToken.objects.create(
            email='me.an@momcare.vn',
            otp_code='123456',
            otp_type='forgot_password',
            expires_at=now + timedelta(minutes=10),
            is_used=False,
        )
        OTPToken.objects.create(
            email='new.user@momcare.vn',
            otp_code='654321',
            otp_type='register',
            expires_at=now - timedelta(minutes=5),
            is_used=False,
        )
        OTPToken.objects.create(
            email='me.bich@momcare.vn',
            otp_code='112233',
            otp_type='forgot_password',
            expires_at=now + timedelta(minutes=2),
            is_used=True,
        )
        self.stdout.write(f'  - Tổng số OTP: {OTPToken.objects.count()}')

    def _seed_admin_logs(self, users, posts, comments):
        self.stdout.write('\n[11] Tạo nhật ký hoạt động admin...')
        AdminActivityLog.objects.filter(admin__username__in=users.keys()).delete()

        log_data = [
            {
                'admin': users['admin_momcare'],
                'action_type': 'settings_change',
                'action_description': 'Cập nhật cấu hình report_threshold từ 5 xuống 3.',
                'status': 'success',
                'ip_address': '127.0.0.1',
            },
            {
                'admin': users['mod_hoa'],
                'action_type': 'report_process',
                'action_description': 'Xử lý báo cáo spam cho bài viết #{}'.format(posts[-1].pk),
                'target_post': posts[-1],
                'status': 'success',
                'ip_address': '127.0.0.1',
            },
            {
                'admin': users['mod_hoa'],
                'action_type': 'comment_hide',
                'action_description': 'Ẩn bình luận có nội dung quảng cáo.',
                'target_comment': comments[-1],
                'status': 'success',
                'ip_address': '127.0.0.1',
            },
        ]

        now = timezone.now()
        for idx, item in enumerate(log_data):
            log = AdminActivityLog.objects.create(**item)
            created_at = now - timedelta(hours=idx + 1)
            AdminActivityLog.objects.filter(pk=log.pk).update(created_at=created_at)

        self.stdout.write(f'  - Tổng số log admin: {AdminActivityLog.objects.count()}')

    def _print_summary(self, users):
        self.stdout.write('\n' + self.style.SUCCESS('=' * 72))
        self.stdout.write(self.style.SUCCESS('SEED HOÀN TẤT'))
        self.stdout.write(self.style.SUCCESS('=' * 72))
        self.stdout.write(f'Category: {Category.objects.count()}')
        self.stdout.write(f'User: {User.objects.count()}')
        self.stdout.write(f'UserProfile: {UserProfile.objects.count()}')
        self.stdout.write(f'Post: {Post.objects.count()}')
        self.stdout.write(f'PostVerification: {PostVerification.objects.count()}')
        self.stdout.write(f'Comment: {Comment.objects.count()}')
        self.stdout.write(f'Report: {Report.objects.count()}')
        self.stdout.write(f'Notification: {Notification.objects.count()}')
        self.stdout.write(f'SystemSettings: {SystemSettings.objects.count()}')
        self.stdout.write(f'OTPToken: {OTPToken.objects.count()}')
        self.stdout.write(f'AdminActivityLog: {AdminActivityLog.objects.count()}')

        self.stdout.write('\nTài khoản demo:')
        self.stdout.write('  - admin_momcare / Admin123!@#')
        self.stdout.write('  - mod_hoa / ModHoa123!@#')
        self.stdout.write('  - bac_si_linh / BacSi123!@#')
        self.stdout.write('  - bac_si_minh / BacSiMinh123!@#')
        self.stdout.write('  - me_an / MeAn123!@#')
        self.stdout.write('  - me_bich / MeBich123!@#')
        self.stdout.write('  - me_cuong / MeCuong123!@#')
        self.stdout.write('  - ba_bau_lan / BaBauLan123!@#')
        self.stdout.write('  - user_spam_01 / SpamUser123!@#')

