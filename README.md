# fiap-bff-signup

BFF responsável por **orquestrar o cadastro**:
1) Cria usuário no **Keycloak** (Admin API, client credentials)
2) Seta senha + atribui roles de realm
3) Cria o comprador no **fiap-srv-buyers** usando `external_id = <keycloak_user_id>`

## Endpoints

### `GET /healthz`
Retorna `{"status":"ok"}`.

### `GET /readyz`
Checagem simples de prontidão.

### `POST /signup`
Cria usuário no Keycloak e o comprador no buyers.

**Body**
```json
{
  "email": "john@example.com",
  "password": "Passw0rd!",
  "full_name": "John Doe",
  "phone": "11999999999",
  "document": "12345678900"
}
