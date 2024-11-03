import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import bcrypt
from sqlalchemy import select, delete
from app.core.config import async_session_factory, init_db
from app.models.models import User, Shop, users_shops
import sys


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("300x150")

        # Center window
        self.root.eval('tk::PlaceWindow . center')

        # Login frame
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Username
        ttk.Label(frame, text="Username:").grid(row=0, column=0, pady=5)
        self.username = ttk.Entry(frame)
        self.username.grid(row=0, column=1, pady=5)

        # Password
        ttk.Label(frame, text="Password:").grid(row=1, column=0, pady=5)
        self.password = ttk.Entry(frame, show="*")
        self.password.grid(row=1, column=1, pady=5)

        # Login button
        ttk.Button(frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)

        # Initialize event loop
        self.loop = asyncio.get_event_loop()

    async def verify_credentials(self, username: str, password: str) -> bool:
        async with async_session_factory() as session:
            query = select(User).where(User.login == username)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user and user.is_superuser and bcrypt.checkpw(password.encode(), user.password.encode()):
                return True
            return False

    def login(self):
        username = self.username.get()
        password = self.password.get()

        if self.loop.run_until_complete(self.verify_credentials(username, password)):
            self.root.destroy()
            app = MainApplication()
            app.root.mainloop()  # Start the mainloop directly instead of calling run()
        else:
            messagebox.showerror("Error", "Invalid credentials")



class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Shop Management System")
        self.root.geometry("800x600")

        # Initialize event loop
        self.loop = asyncio.get_event_loop()

        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.users_tab = ttk.Frame(self.notebook)
        self.shops_tab = ttk.Frame(self.notebook)
        self.assignments_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.users_tab, text='Users')
        self.notebook.add(self.shops_tab, text='Shops')
        self.notebook.add(self.assignments_tab, text='Assignments')

        self.setup_users_tab()
        self.setup_shops_tab()
        self.setup_assignments_tab()

        # Initial data load
        self.refresh_all_data()
    def setup_users_tab(self):
        # Users list
        self.users_tree = ttk.Treeview(self.users_tab, columns=('ID', 'Login', 'Email', 'Is Admin'), show='headings')
        self.users_tree.heading('ID', text='ID')
        self.users_tree.heading('Login', text='Login')
        self.users_tree.heading('Email', text='Email')
        self.users_tree.heading('Is Admin', text='Is Admin')
        self.users_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Buttons frame
        btn_frame = ttk.Frame(self.users_tab)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(btn_frame, text="Add User", command=self.show_add_user_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete User", command=self.delete_user).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_users).pack(side='left', padx=5)

    def setup_shops_tab(self):
        # Shops list
        self.shops_tree = ttk.Treeview(self.shops_tab, columns=('ID', 'Name', 'Is Active'), show='headings')
        self.shops_tree.heading('ID', text='ID')
        self.shops_tree.heading('Name', text='Name')
        self.shops_tree.heading('Is Active', text='Is Active')
        self.shops_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Buttons frame
        btn_frame = ttk.Frame(self.shops_tab)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(btn_frame, text="Add Shop", command=self.show_add_shop_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete Shop", command=self.delete_shop).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_shops).pack(side='left', padx=5)

    def setup_assignments_tab(self):
        # Create frames
        left_frame = ttk.Frame(self.assignments_tab)
        right_frame = ttk.Frame(self.assignments_tab)

        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Users list with assignments
        ttk.Label(left_frame, text="Users").pack()
        self.assign_users_tree = ttk.Treeview(
            left_frame,
            columns=('ID', 'Login', 'Assigned Shops'),
            show='headings'
        )
        self.assign_users_tree.heading('ID', text='ID')
        self.assign_users_tree.heading('Login', text='Login')
        self.assign_users_tree.heading('Assigned Shops', text='Assigned Shops')
        self.assign_users_tree.pack(fill='both', expand=True)

        # Shops list with assignments
        ttk.Label(right_frame, text="Shops").pack()
        self.assign_shops_tree = ttk.Treeview(
            right_frame,
            columns=('ID', 'Name', 'Assigned Users'),
            show='headings'
        )
        self.assign_shops_tree.heading('ID', text='ID')
        self.assign_shops_tree.heading('Name', text='Name')
        self.assign_shops_tree.heading('Assigned Users', text='Assigned Users')
        self.assign_shops_tree.pack(fill='both', expand=True)

        # Buttons frame
        btn_frame = ttk.Frame(self.assignments_tab)
        btn_frame.pack(side='bottom', fill='x', padx=5, pady=5)

        ttk.Button(btn_frame, text="Assign User to Shop", command=self.assign_user_to_shop).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Assignment", command=self.remove_assignment).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_assignments).pack(side='left', padx=5)

    async def _add_user(self, login: str, password: str, email: str, is_admin: bool):
        async with async_session_factory() as session:
            # Проверяем только уникальность логина
            query = select(User).where(User.login == login)
            existing_user = await session.execute(query)
            if existing_user.scalar_one_or_none():
                raise ValueError("User with this login already exists")

            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            new_user = User(
                login=login,
                password=hashed_password,
                email=email,
                is_superuser=is_admin
            )
            session.add(new_user)
            await session.commit()

    def show_add_user_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add User")
        dialog.geometry("300x250")

        ttk.Label(dialog, text="Login:").pack(pady=5)
        login_entry = ttk.Entry(dialog)
        login_entry.pack(pady=5)

        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)

        ttk.Label(dialog, text="Email:").pack(pady=5)
        email_entry = ttk.Entry(dialog)
        email_entry.pack(pady=5)

        is_admin_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="Is Admin", variable=is_admin_var).pack(pady=5)

        def add_user():
            try:
                self.loop.run_until_complete(self._add_user(
                    login_entry.get(),
                    password_entry.get(),
                    email_entry.get(),
                    is_admin_var.get()
                ))
                dialog.destroy()
                self.refresh_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Add", command=add_user).pack(pady=10)

    async def _delete_user(self, user_id: int):
        async with async_session_factory() as session:
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()

    def delete_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this user?"):
            user_id = self.users_tree.item(selected[0])['values'][0]
            try:
                self.loop.run_until_complete(self._delete_user(user_id))
                self.refresh_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    async def _add_shop(self, name: str):
        async with async_session_factory() as session:
            new_shop = Shop(name=name)
            session.add(new_shop)
            await session.commit()

    def show_add_shop_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Shop")
        dialog.geometry("300x150")

        ttk.Label(dialog, text="Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(pady=5)

        def add_shop():
            try:
                self.loop.run_until_complete(self._add_shop(name_entry.get()))
                dialog.destroy()
                self.refresh_shops()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Add", command=add_shop).pack(pady=10)

    async def _delete_shop(self, shop_id: int):
        async with async_session_factory() as session:
            await session.execute(delete(Shop).where(Shop.id == shop_id))
            await session.commit()

    def delete_shop(self):
        selected = self.shops_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a shop to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this shop?"):
            shop_id = self.shops_tree.item(selected[0])['values'][0]
            try:
                self.loop.run_until_complete(self._delete_shop(shop_id))
                self.refresh_shops()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    async def _assign_user_to_shop(self, user_id: int, shop_id: int):
        async with async_session_factory() as session:
            # Проверяем, существует ли уже такая связь
            query = select(users_shops).where(
                users_shops.c.user_id == user_id,
                users_shops.c.shop_id == shop_id
            )
            result = await session.execute(query)
            if result.first():
                raise ValueError("This user is already assigned to this shop")

            # Создаем новую связь
            stmt = users_shops.insert().values(
                user_id=user_id,
                shop_id=shop_id
            )
            await session.execute(stmt)
            await session.commit()
    def assign_user_to_shop(self):
        selected_user = self.assign_users_tree.selection()
        selected_shop = self.assign_shops_tree.selection()

        if not selected_user or not selected_shop:
            messagebox.showwarning("Warning", "Please select both user and shop")
            return

        user_id = self.assign_users_tree.item(selected_user[0])['values'][0]
        shop_id = self.assign_shops_tree.item(selected_shop[0])['values'][0]

        try:
            self.loop.run_until_complete(self._assign_user_to_shop(user_id, shop_id))
            self.refresh_assignments()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    async def _remove_assignment(self, user_id: int, shop_id: int):
        async with async_session_factory() as session:
            await session.execute(
                delete(users_shops).where(
                    users_shops.c.user_id == user_id,
                    users_shops.c.shop_id == shop_id
                )
            )
            await session.commit()

    def remove_assignment(self):
        selected_user = self.assign_users_tree.selection()
        selected_shop = self.assign_shops_tree.selection()

        if not selected_user or not selected_shop:
            messagebox.showwarning("Warning", "Please select both user and shop")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to remove this assignment?"):
            user_id = self.assign_users_tree.item(selected_user[0])['values'][0]
            shop_id = self.assign_shops_tree.item(selected_shop[0])['values'][0]

            try:
                self.loop.run_until_complete(self._remove_assignment(user_id, shop_id))
                self.refresh_assignments()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    async def _get_shops(self):
        """Получение списка магазинов из базы данных"""
        async with async_session_factory() as session:
            result = await session.execute(select(Shop))
            return result.scalars().all()

    async def _get_users(self):
        """Получение списка пользователей из базы данных"""
        async with async_session_factory() as session:
            result = await session.execute(select(User))
            return result.scalars().all()

    async def _get_user_shops(self):
        """Получение списка связей пользователей и магазинов"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(users_shops)
                .join(User, users_shops.c.user_id == User.id)
                .join(Shop, users_shops.c.shop_id == Shop.id)
            )
            return result.all()

    def refresh_shops(self):
        """Обновление списка магазинов в интерфейсе"""
        # Clear existing items
        for item in self.shops_tree.get_children():
            self.shops_tree.delete(item)

        try:
            # Fetch and display shops
            shops = self.loop.run_until_complete(self._get_shops())
            for shop in shops:
                self.shops_tree.insert('', 'end', values=(
                    shop.id,
                    shop.name,
                    'Yes' if shop.is_active else 'No'
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh shops: {str(e)}")

    def refresh_users(self):
        """Обновление списка пользователей в интерфейсе"""
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        try:
            # Fetch and display users
            users = self.loop.run_until_complete(self._get_users())
            for user in users:
                self.users_tree.insert('', 'end', values=(
                    user.id,
                    user.login,
                    user.email,
                    'Yes' if user.is_superuser else 'No'
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh users: {str(e)}")

    def refresh_assignments(self):
        """Обновление списка назначений в интерфейсе"""
        # Clear existing items
        for item in self.assign_users_tree.get_children():
            self.assign_users_tree.delete(item)
        for item in self.assign_shops_tree.get_children():
            self.assign_shops_tree.delete(item)

        try:
            # Fetch data
            users = self.loop.run_until_complete(self._get_users())
            shops = self.loop.run_until_complete(self._get_shops())
            assignments = self.loop.run_until_complete(self._get_user_shops())

            # Create a set of tuples for quick lookup
            assigned_pairs = {(a.user_id, a.shop_id) for a in assignments}

            # Display users with their assignments
            for user in users:
                shop_names = [
                    s.name for s in shops
                    if (user.id, s.id) in assigned_pairs
                ]
                self.assign_users_tree.insert('', 'end', values=(
                    user.id,
                    user.login,
                    ', '.join(shop_names) if shop_names else 'No assignments'
                ))

            # Display shops with their assignments
            for shop in shops:
                user_names = [
                    u.login for u in users
                    if (u.id, shop.id) in assigned_pairs
                ]
                self.assign_shops_tree.insert('', 'end', values=(
                    shop.id,
                    shop.name,
                    ', '.join(user_names) if user_names else 'No assignments'
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh assignments: {str(e)}")

    def refresh_all_data(self):
        """Обновление всех данных в интерфейсе"""
        try:
            self.refresh_users()
            self.refresh_shops()
            self.refresh_assignments()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")


async def create_admin_if_not_exists():
    """Create default admin user if it doesn't exist"""
    async with async_session_factory() as session:
        # Check if admin exists
        query = select(User).where(User.login == 'admin')
        result = await session.execute(query)
        admin = result.scalar_one_or_none()

        if not admin:
            # Create admin user
            hashed_password = bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()).decode()
            admin = User(
                login='admin',
                password=hashed_password,
                email='admin@example.com',
                is_superuser=True
            )
            session.add(admin)
            await session.commit()


def main():
    # Set up asyncio event loop
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop()

    try:
        # Initialize database
        loop.run_until_complete(init_db())

        # Create admin user if it doesn't exist
        loop.run_until_complete(create_admin_if_not_exists())

        # Start application
        login_window = LoginWindow()
        login_window.root.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()