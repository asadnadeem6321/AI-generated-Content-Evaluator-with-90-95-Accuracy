from rest_framework import serializers

class ClassStatisticsSerializer(serializers.Serializer):
    '''Class level stats'''
    class_id = serializers.UUIDField()
    class_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    completed_submissions = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_grammar_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    high_ai_count = serializers.IntegerField()  # if Submissions >70% 


class StudentPerformanceSerializer(serializers.Serializer):
    '''Individual student stats'''
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_email = serializers.EmailField()
    total_submissions = serializers.IntegerField()
    average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_grammar_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    flagged_submissions = serializers.IntegerField()
    last_submission = serializers.DateTimeField()


class SubmissionTimelineSerializer(serializers.Serializer):
    """Daily/weekly submission trends"""
    date = serializers.DateField()
    submission_count = serializers.IntegerField()
    average_ai_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class AIDistributionSerializer(serializers.Serializer):
    """AI percentage distribution"""
    range_label = serializers.CharField()  # "0-30%", "30-50%", ...
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)