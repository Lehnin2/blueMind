# Guide d'authentification avec Supabase

Ce module fournit une intégration d'authentification pour l'application TraeFishing en utilisant Supabase.

## Configuration de Supabase

1. Créez un compte sur [Supabase](https://supabase.com/) si vous n'en avez pas déjà un.

2. Créez un nouveau projet dans Supabase:
   - Donnez un nom à votre projet (ex: "traefishing")
   - Choisissez un mot de passe pour la base de données
   - Sélectionnez la région la plus proche de vos utilisateurs

3. Une fois le projet créé, accédez aux informations d'API:
   - Dans le tableau de bord Supabase, allez dans "Settings" > "API"
   - Copiez l'URL du projet et la clé anon/public

4. Mettez à jour le fichier de configuration:
   - Ouvrez `app/config/api_keys.json`
   - Remplacez les valeurs suivantes par vos propres clés:
     ```json
     "SUPABASE_URL": "https://your-supabase-project-id.supabase.co",
     "SUPABASE_KEY": "your-supabase-anon-key"
     ```

## Structure de la base de données

Supabase crée automatiquement une table `auth.users` pour gérer les utilisateurs. Vous pouvez créer des tables supplémentaires pour stocker des informations spécifiques à votre application.

Exemple de table pour les profils utilisateurs:

```sql
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  updated_at timestamp with time zone,
  username text unique,
  full_name text,
  avatar_url text,
  website text,
  
  constraint username_length check (char_length(username) >= 3)
);

-- Créer une politique RLS (Row Level Security)
alter table public.profiles enable row level security;

create policy "Les profils utilisateurs sont visibles par tous."
  on profiles for select
  using ( true );

create policy "Les utilisateurs peuvent insérer leur propre profil."
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Les utilisateurs peuvent mettre à jour leur propre profil."
  on profiles for update
  using ( auth.uid() = id );

-- Fonction pour créer automatiquement un profil après inscription
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  return new;
end;
$$;

-- Trigger pour appeler la fonction après création d'un utilisateur
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

## Utilisation de l'authentification

L'application dispose maintenant de routes pour:

- `/login` - Page de connexion
- `/register` - Page d'inscription
- `/api/login` - API pour la connexion
- `/api/register` - API pour l'inscription
- `/api/logout` - API pour la déconnexion

Pour protéger une route et exiger l'authentification, vous pouvez utiliser un middleware comme ceci:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.supabase_client import SupabaseClient

security = HTTPBearer()
supabase = SupabaseClient()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = supabase.get_user(token)
    if "error" in user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Utilisation dans une route
@app.get("/protected-route")
async def protected_route(user = Depends(get_current_user)):
    return {"message": f"Hello, {user['email']}!"}
```

## Résolution de l'erreur d'importation

L'erreur d'importation du module `retriverloi1` a été corrigée en ajoutant le répertoire parent au chemin d'importation Python dans les fichiers qui utilisent ce module.