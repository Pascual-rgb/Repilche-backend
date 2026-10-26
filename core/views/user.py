from rest_framework import generics, permissions
from core.serializers import UserDetailSerializer


class UsuarioMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user