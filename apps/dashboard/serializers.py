from rest_framework import serializers

class ClassStatisticsSerializer(serializers.Serializer):
    """Class-level statistics"""
    class_id = serializers.UUIDField()
    class_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    completed_submissions = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_grammar_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    high_ai_count = serializers.IntegerField()


class StudentPerformanceSerializer(serializers.Serializer):
    """Student performance across assignments"""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_email = serializers.EmailField()
    total_submissions = serializers.IntegerField()
    completed_submissions = serializers.IntegerField()
    average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_grammar_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    flagged_submissions = serializers.IntegerField()


class SubmissionOverviewSerializer(serializers.Serializer):
    """Overview of submissions for an assignment"""
    submission_id = serializers.UUIDField()
    student_name = serializers.CharField()
    student_email = serializers.EmailField()
    submitted_at = serializers.DateTimeField()
    status = serializers.CharField()
    processing_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    grammar_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    is_flagged = serializers.BooleanField()


class AssignmentStatisticsSerializer(serializers.Serializer):
    """Assignment-level statistics"""
    assignment_id = serializers.UUIDField()
    assignment_title = serializers.CharField()
    deadline = serializers.DateTimeField()
    is_past_deadline = serializers.BooleanField()
    total_students = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    high_ai_submissions = serializers.IntegerField()

# class SubmissionTimelineSerializer(serializers.Serializer):
#     """Daily/weekly submission trends"""
#     date = serializers.DateField()
#     submission_count = serializers.IntegerField()
#     average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


# class AIDistributionSerializer(serializers.Serializer):
#     """AI percentage distribution"""
#     range_label = serializers.CharField()  # "0-30%", "30-50%", ...
#     count = serializers.IntegerField()
#     percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
