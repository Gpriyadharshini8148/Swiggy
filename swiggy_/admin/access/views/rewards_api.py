from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import Rewards
from admin.access.serializers import RewardsSerializer
from ..permissions import IsAuthenticatedUser
from django.db.models import Sum

class RewardsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rewards.objects.all()
    serializer_class = RewardsSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Rewards.objects.all()
        user_id = self.request.session.get('user_id')
        if not user_id:
            return Rewards.objects.none()
        return Rewards.objects.filter(user_id=user_id)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        rewards = Rewards.objects.filter(user_id=user_id)
        earned = rewards.aggregate(Sum('points_earned'))['points_earned__sum'] or 0
        redeemed = rewards.aggregate(Sum('points_redeemed'))['points_redeemed__sum'] or 0
        balance = earned - redeemed
        return Response({"balance": balance, "earned": earned, "redeemed": redeemed})

    @action(detail=False, methods=['post'])
    def redeem(self, request):
        user_id = request.session.get('user_id')
        points = request.data.get('points')
        if not user_id:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        if not points:
            return Response({"error": "Points amount required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            points = int(points)
            if points <= 0:
                return Response({"error": "Points must be positive"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid points value"}, status=status.HTTP_400_BAD_REQUEST)
        rewards = Rewards.objects.filter(user_id=user_id)
        earned = rewards.aggregate(Sum('points_earned'))['points_earned__sum'] or 0
        redeemed = rewards.aggregate(Sum('points_redeemed'))['points_redeemed__sum'] or 0
        balance = earned - redeemed
        if points > balance:
            return Response({"error": "Insufficient balance", "current_balance": balance}, status=status.HTTP_400_BAD_REQUEST)
        Rewards.objects.create(user_id=user_id, points_redeemed=points, points_earned=0)
        return Response({"message": "Redeemed successfully", "redeemed_points": points, "new_balance": balance - points})
