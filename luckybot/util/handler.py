import vk
import random
import datetime
from collections import Counter


class Handler:
    def __init__(self, db, mc, city, category, group_id, max_contest_count, max_contest_days):
        self.db = db
        self.mc = mc
        self.city = city
        self.category = category
        self.group_id = group_id
        self.max_contest_count = max_contest_count
        self.max_contest_days = max_contest_days

        self.city_keyword = lambda user_id: "city_%d" % user_id
        self.category_keyword = lambda user_id: "category_%d" % user_id
        self.gift_keyword = lambda user_id: "gift_%d" % user_id

        session = vk.Session()
        self.vk_api = vk.API(session, v='5.67', lang='ru')

        self.handlers = dict(
            add=self.add,
            delete=self.delete,
            show=self.show,
            group_join=self.group_join,
            group_leave=self.group_leave,
            show_contest=self.show_contest,
            show_contest_city=self.show_contest_city,
            show_contest_category=self.show_contest_category,
            show_contest_gift=self.show_contest_gift,
            show_city=self.show_city,
            show_category=self.show_category,
            show_gift=self.show_gift,
            contest=self.show_contest,
            contest_city=self.show_contest_city,
            contest_category=self.show_contest_category,
            contest_gift=self.show_contest_gift,
            city=self.show_city,
            category=self.show_category,
            gift=self.show_gift,
            add_city=self.add_city,
            add_category=self.add_category,
            add_gift=self.add_gift,
            delete_city=self.delete_city,
            delete_category=self.delete_category,
            delete_gift=self.delete_gift,
            help=self.help
        )

    async def get_or_create_user(self, user_id):
        try:
            user = await self.db.user.find_one({'user_id': user_id})
            if not user:
                is_member = True if self.vk_api.groups.isMember(group_id=self.group_id, user_id=user_id) else False
                data = self.vk_api.users.get(user_id=user_id, fields='city')[0]
                city = [data['city']['id']] if 'city' in data and self.city.exist(data['city']['id']) else []
                user = dict(
                    user_id=user_id,
                    city=city,
                    category=[],
                    gift=[],
                    is_member=is_member
                )
                await self.db.user.insert_one(user)
            return user
        except Exception as msg:
            return self.get_or_create_user(user_id)

    async def help(self, user_id, data):
        return dict(
            type='help',
            user_id=user_id
        )

    async def group_join(self, user_id, data):
        await self.db.user.update_one({'user_id': user_id}, {'$set': {'is_member': True}}, upsert=False)
        return dict(
            type='group_join',
            user_id=user_id
        )

    async def group_leave(self, user_id, data):
        await self.db.user.update_one({'user_id': user_id}, {'$set': {'is_member': False}}, upsert=False)
        return dict(
            type='group_leave',
            user_id=user_id
        )

    async def add(self, user_id, data):
        return dict(
            type='help_add',
            user_id=user_id
        )

    async def delete(self, user_id, data):
        return dict(
            type='help_delete',
            user_id=user_id
        )

    async def show(self, user_id, data):
        return dict(
            type='help_show',
            user_id=user_id
        )

    async def add_city(self, user_id, data):
        user_city = await self.mc.get(self.city_keyword(user_id))
        if not user_city:
            user = await self.get_or_create_user(user_id)
            user_city = set(user['city'])
        count = 0
        for city in data['city']:
            if city not in user_city:
                user_city.add(city)
                count += 1
        await self.db.user.update({'user_id': user_id}, {'$set': {'city': list(user_city)}}, upsert=False)
        await self.mc.set(self.city_keyword(user_id), user_city)
        return dict(
            type='not_add_city' if not count else ('add_city' if count == 1 else 'add_cities'),
            user_id=user_id
        )

    async def add_category(self, user_id, data):
        user_category = await self.mc.get(self.category_keyword(user_id))
        if not user_category:
            user = await self.get_or_create_user(user_id)
            user_category = set(user['category'])
        count = 0
        data['category'].sort()
        main_categories = set()
        for category in data['category']:
            if category not in user_category:
                user_category.add(category)
                if ':' in category:
                    main_categories.add(category.split(':')[0])
                else:
                    for item in self.category.data[category]['child']:
                        key = "%s:%s" % (category, item)
                        if key not in user_category:
                            user_category.add(key)
                count += 1
        counter = Counter(map(lambda x: x.split(':')[0], user_category))
        for category in main_categories:
            if counter[category] == len(self.category.data[category]['child']):
                user_category.add(category)
        await self.db.user.update({'user_id': user_id}, {'$set': {'category': list(user_category)}}, upsert=False)
        await self.mc.set(self.category_keyword(user_id), user_category)
        return dict(
            type='not_add_category' if not count else ('add_category' if count == 1 else 'add_categories'),
            user_id=user_id
        )

    async def add_gift(self, user_id, data):
        user_gift = await self.mc.get(self.gift_keyword(user_id))
        if not user_gift:
            user = await self.get_or_create_user(user_id)
            user_gift = set(user['gift'])
        count = 0
        for gift in data['gift']:
            if gift not in user_gift:
                user_gift.add(gift)
                count += 1
        await self.db.user.update({'user_id': user_id}, {'$set': {'gift': list(user_gift)}}, upsert=False)
        await self.mc.set(self.gift_keyword(user_id), user_gift)
        return dict(
            type='not_add_gift' if not count else ('add_gift' if count == 1 else 'add_gifts'),
            user_id=user_id
        )

    async def delete_city(self, user_id, data):
        user_city = await self.mc.get(self.city_keyword(user_id))
        if not user_city:
            user = await self.get_or_create_user(user_id)
            user_city = set(user['city'])
        count = 0
        for city in data['city']:
            if city in user_city:
                user_city.remove(city)
                count += 1
        await self.db.user.update({'user_id': user_id}, {'$set': {'city': list(user_city)}}, upsert=False)
        await self.mc.set(self.city_keyword(user_id), user_city)
        return dict(
            type='not_delete_city' if not count else ('delete_city' if count == 1 else 'delete_cities'),
            user_id=user_id
        )

    async def delete_category(self, user_id, data):
        user_category = await self.mc.get(self.category_keyword(user_id))
        if not user_category:
            user = await self.get_or_create_user(user_id)
            user_category = set(user['category'])
        count = 0
        for category in data['category']:
            if category in user_category:
                if ':' in category:
                    user_category.remove(category)
                    root_category = category.split(':')[0]
                    if root_category in user_category:
                        user_category.remove(root_category)
                else:
                    for item in self.category.data[category]['child']:
                        key = '%s:%s' % (category, item)
                        if key in user_category:
                            user_category.remove(key)
                    user_category.remove(category)
                count += 1
        await self.db.user.update({'user_id': user_id}, {'$set': {'category': list(user_category)}}, upsert=False)
        await self.mc.set(self.category_keyword(user_id), user_category)
        return dict(
            type='not_delete_category' if not count else ('delete_category' if count == 1 else 'delete_categories'),
            user_id=user_id
        )

    async def delete_gift(self, user_id, data):
        user_gift = await self.mc.get(self.gift_keyword(user_id))
        if not user_gift:
            user = await self.get_or_create_user(user_id)
            user_gift = set(user['gift'])
        count = 0
        for gift in data['gift']:
            if gift in user_gift:
                user_gift.remove(gift)
                count += 1
        await self.db.user.update({'user_id': user_id}, {'$set': {'gift': list(user_gift)}}, upsert=False)
        await self.mc.set(self.gift_keyword(user_id), user_gift)
        return dict(
            type='not_delete_gift' if not count else ('delete_gift' if count == 1 else 'delete_gifts'),
            user_id=user_id
        )

    async def show_city(self, user_id, data):
        user_city = await self.mc.get(self.city_keyword(user_id))
        if not user_city:
            user = await self.get_or_create_user(user_id)
            user_city = set(user['city'])
            await self.mc.set(self.city_keyword(user_id), user_city)
        return dict(
            type='show_city',
            user_id=user_id,
            data=', '.join(map(lambda city_id: self.city.get_title(city_id), user_city))
        )

    async def show_category(self, user_id, data):
        user_category = await self.mc.get(self.category_keyword(user_id))
        if not user_category:
            user = await self.get_or_create_user(user_id)
            user_category = set(user['category'])
            await self.mc.set(self.category_keyword(user_id), user_category)
        return dict(
            type='show_category',
            user_id=user_id,
            data=self.category.get_categories(user_category)
        )

    async def show_gift(self, user_id, data):
        user_gift = await self.mc.get(self.gift_keyword(user_id))
        if not user_gift:
            user = await self.get_or_create_user(user_id)
            user_gift = set(user['gift'])
            await self.mc.set(self.gift_keyword(user_id), user_gift)
        return dict(
            type='show_gift',
            user_id=user_id,
            data=', '.join(map(lambda x: '"%s"' % x, user_gift))
        )

    async def show_contest(self, user_id, data):
        pass

    async def show_contest_city(self, user_id, data):
        pass

    async def show_contest_category(self, user_id, data):
        pass

    async def show_contest_gift(self, user_id, data):
        user_city = await self.mc.get(self.city_keyword(user_id))
        if not user_city:
            user = await self.get_or_create_user(user_id)
            user_city = set(user['city'])
            await self.mc.set(self.city_keyword(user_id), user_city)
        if data['gift']:
            user_gift = data['gift']
        else:
            user_gift = await self.mc.get(self.gift_keyword(user_id))
            if not user_gift:
                user = await self.get_or_create_user(user_id)
                user_gift = set(user['gift'])
                await self.mc.set(self.gift_keyword(user_id), user_gift)
        random.shuffle(user_gift)
        current_date = datetime.datetime.now()
        current_date -= datetime.timedelta(hours=current_date.hour, minutes=current_date.minute,
                                           seconds=current_date.second, microseconds=current_date.microsecond)
        contest = await self.db.contest.aggregate(
            [
                {
                    '$match':
                        {
                            '$and':
                                [
                                    {
                                        'date':
                                            {
                                                '$gte': current_date
                                            }
                                    },
                                    {
                                        'date':
                                            {
                                                '$lt': current_date + datetime.timedelta(days=self.max_contest_days)
                                            }
                                    },
                                    {
                                        '$text':
                                            {
                                                '$search': ' '.join(user_gift),
                                                '$language': 'ru'
                                            }
                                    },
                                    {
                                        '$or': [
                                            {
                                                'city':
                                                    {
                                                        '$size': 0
                                                    }
                                            },
                                            {
                                                'city':
                                                    {
                                                        '$in': user_city
                                                    }
                                            }
                                        ]
                                    }
                                ]
                        }
                },
                {
                    '$sample':
                        {
                            'size': self.max_contest_count
                        }
                }
            ]
        )
        return dict(
            type='show_contest_gift',
            user_id=user_id,
            data=list(map(lambda x: 'https://vk.com/wall%s' % contest['post_id'], contest))
        )
