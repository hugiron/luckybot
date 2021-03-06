import vk
import random
import datetime
from collections import Counter

from luckybot.util.normalizer import Normalizer


class Handler:
    def __init__(self, db, memcached, city, category, group_id, max_contest_count, max_contest_days):
        self.db = db
        self.memcached = memcached
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
        self.normalizer = Normalizer()

        self.handlers = dict(
            message_allow=self.message_allow,
            thanks=self.thanks,
            greeting=self.greeting,
            group_join=self.group_join,
            group_leave=self.group_leave,
            add=self.add,
            delete=self.delete,
            contest=self.show_contest,
            city=self.show_city,
            category=self.show_category,
            gift=self.show_gift,
            help=self.help
        )

    async def get_user_city(self, user_id):
        user_city = self.memcached.get(self.city_keyword(user_id))
        if not user_city:
            user = await self.get_or_create_user(user_id)
            user_city = user['city']
            self.memcached.set(self.city_keyword(user_id), user_city)
        return user_city

    async def set_user_city(self, user_id, user_city):
        await self.db.user.update({'user_id': user_id}, {'$set': {'city': user_city}}, upsert=False)
        self.memcached.set(self.city_keyword(user_id), user_city)

    async def get_user_category(self, user_id):
        user_category = self.memcached.get(self.category_keyword(user_id))
        if not user_category:
            user = await self.get_or_create_user(user_id)
            user_category = user['category']
            self.memcached.set(self.category_keyword(user_id), user_category)
        return user_category

    async def set_user_category(self, user_id, user_category):
        await self.db.user.update({'user_id': user_id}, {'$set': {'category': user_category}}, upsert=False)
        self.memcached.set(self.category_keyword(user_id), user_category)

    async def get_user_gift(self, user_id):
        user_gift = self.memcached.get(self.gift_keyword(user_id))
        if not user_gift:
            user = await self.get_or_create_user(user_id)
            user_gift = user['gift']
            self.memcached.set(self.gift_keyword(user_id), user_gift)
        return user_gift

    async def set_user_gift(self, user_id, user_gift):
        await self.db.user.update({'user_id': user_id}, {'$set': {'gift': user_gift}}, upsert=False)
        self.memcached.set(self.gift_keyword(user_id), user_gift)

    @staticmethod
    def render_contest(contest):
        result = list()
        for index, item in enumerate(contest):
            result.append('https://vk.com/wall%s' % item['post_id'])
        return result

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
        await self.get_or_create_user(user_id)
        return dict(
            type='help',
            user_id=user_id
        )

    async def thanks(self, user_id, data):
        await self.get_or_create_user(user_id)
        return dict(
            type='thanks',
            user_id=user_id
        )

    async def message_allow(self, user_id, data):
        await self.get_or_create_user(user_id)
        return dict(
            type='greeting',
            user_id=user_id
        )

    async def greeting(self, user_id, data):
        await self.get_or_create_user(user_id)
        return dict(
            type='greeting',
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
        if data:
            result = list()
            if data.get('city'):
                result.append(await self.add_city(user_id, data))
            if data.get('category'):
                result.append(await self.add_category(user_id, data))
            if data.get('gift'):
                result.append(await self.add_gift(user_id, data))
            if result:
                return result
        await self.get_or_create_user(user_id)
        return dict(
            type='help_add',
            user_id=user_id
        )

    async def delete(self, user_id, data):
        if data:
            result = list()
            if data.get('city'):
                result.append(await self.delete_city(user_id, data))
            if data.get('category'):
                result.append(await self.delete_category(user_id, data))
            if data.get('gift'):
                result.append(await self.delete_gift(user_id, data))
            if result:
                return result
        await self.get_or_create_user(user_id)
        return dict(
            type='help_delete',
            user_id=user_id
        )

    async def add_city(self, user_id, data):
        user_city = await self.get_user_city(user_id)
        user_city = set(user_city)
        count = 0
        for city in data['city']:
            if city not in user_city:
                user_city.add(city)
                count += 1
        user_city = list(user_city)
        await self.set_user_city(user_id, user_city)
        return dict(
            type='not_add_city' if not count else ('add_city' if count == 1 else 'add_cities'),
            user_id=user_id
        )

    async def add_category(self, user_id, data):
        user_category = await self.get_user_category(user_id)
        user_category = set(user_category)
        count = 0
        data['category'].sort()
        main_categories = set()
        for category in data['category']:
            if category not in user_category:
                user_category.add(category)
                if ':' in category:
                    main_categories.add(category.split(':')[0])
                else:
                    if 'child' in self.category.data[category]:
                        for item in self.category.data[category]['child']:
                            key = "%s:%s" % (category, item)
                            if key not in user_category:
                                user_category.add(key)
                count += 1
        counter = Counter(map(lambda x: x.split(':')[0], user_category))
        for category in main_categories:
            if counter[category] == len(self.category.data[category]['child']):
                user_category.add(category)
        user_category = list(user_category)
        await self.set_user_category(user_id, user_category)
        return dict(
            type='not_add_category' if not count else ('add_category' if count == 1 else 'add_categories'),
            user_id=user_id
        )

    async def add_gift(self, user_id, data):
        user_gift = await self.get_user_gift(user_id)
        user_gift = set(user_gift)
        count = 0
        for gift in data['gift']:
            if gift not in user_gift:
                user_gift.add(gift)
                count += 1
        user_gift = list(user_gift)
        await self.set_user_gift(user_id, user_gift)
        return dict(
            type='not_add_gift' if not count else ('add_gift' if count == 1 else 'add_gifts'),
            user_id=user_id
        )

    async def delete_city(self, user_id, data):
        user_city = await self.get_user_city(user_id)
        user_city = set(user_city)
        count = 0
        for city in data['city']:
            if city in user_city:
                user_city.remove(city)
                count += 1
        user_city = list(user_city)
        await self.set_user_city(user_id, user_city)
        return dict(
            type='not_delete_city' if not count else ('delete_city' if count == 1 else 'delete_cities'),
            user_id=user_id
        )

    async def delete_category(self, user_id, data):
        user_category = await self.get_user_category(user_id)
        user_category = set(user_category)
        count = 0
        for category in data['category']:
            if category in user_category:
                if ':' in category:
                    user_category.remove(category)
                    root_category = category.split(':')[0]
                    if root_category in user_category:
                        user_category.remove(root_category)
                else:
                    if 'child' in self.category.data[category]:
                        for item in self.category.data[category]['child']:
                            key = '%s:%s' % (category, item)
                            if key in user_category:
                                user_category.remove(key)
                    user_category.remove(category)
                count += 1
        user_category = list(user_category)
        await self.set_user_category(user_id, user_category)
        return dict(
            type='not_delete_category' if not count else ('delete_category' if count == 1 else 'delete_categories'),
            user_id=user_id
        )

    async def delete_gift(self, user_id, data):
        user_gift = await self.get_user_gift(user_id)
        user_gift = set(user_gift)
        count = 0
        for gift in data['gift']:
            if gift in user_gift:
                user_gift.remove(gift)
                count += 1
        user_gift = list(user_gift)
        await self.set_user_gift(user_id, user_gift)
        return dict(
            type='not_delete_gift' if not count else ('delete_gift' if count == 1 else 'delete_gifts'),
            user_id=user_id
        )

    async def show_city(self, user_id, data):
        user_city = await self.get_user_city(user_id)
        if user_city:
            data = ', '.join(map(lambda city_id: self.city.get_title(city_id), user_city))
        else:
            data = '<не найдено>'
        return dict(
            type='show_city',
            user_id=user_id,
            data=data
        )

    async def show_category(self, user_id, data):
        user_category = await self.get_user_category(user_id)
        return dict(
            type='show_category',
            user_id=user_id,
            data=self.category.get_categories(user_category)
        )

    async def show_gift(self, user_id, data):
        user_gift = await self.get_user_gift(user_id)
        if user_gift:
            data = ', '.join(map(lambda x: '"%s"' % x, user_gift))
        else:
            data = '<не найдено>'
        return dict(
            type='show_gift',
            user_id=user_id,
            data=data
        )

    async def show_contest(self, user_id, data):
        contest = list()
        if data:
            custom_contest = await self.search_contest_custom(user_id, data)
            for item in custom_contest:
                contest.append(item)
        else:
            batch_size = self.max_contest_count // 3
            gift_contest = await self.search_contest_gift(user_id, None, batch_size)
            category_contest = await self.search_contest_category(user_id, None, self.max_contest_count - len(gift_contest) - batch_size)
            random_contest = await self.search_contest_random(user_id, None, self.max_contest_count - len(gift_contest) - len(category_contest))
            buffer = set()
            for item in gift_contest + category_contest + random_contest:
                if item['post_id'] not in buffer:
                    contest.append(item)
                    buffer.add(item['post_id'])
            random.shuffle(contest)
        return dict(
            type='show_contest' if contest else 'not_show_contest',
            user_id=user_id,
            data=Handler.render_contest(contest)
        )

    async def search_contest_custom(self, user_id, data, count=None):
        if 'city' in data and not data['city']:
            data['city'] = await self.get_user_city(user_id)
        if 'category' in data and not data['category']:
            data['category'] = await self.get_user_category(user_id)
        if 'gift' in data and not data['gift']:
            data['gift'] = await self.get_user_gift(user_id)

        current_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

        query_or = list()
        if 'category' in data:
            query_or.append({'category': {'$in': data['category']}})
        if 'gift' in data:
            text_search = '"%s"' % data['gift'][0] if len(data['gift']) == 1 else ' '.join(data['gift'])
            query_or.append({'$text': {'$search': text_search, '$language': 'ru'}})

        query_and = [
            {'date': {'$gte': current_date}},
            {'date': {'$lt': current_date + datetime.timedelta(days=self.max_contest_days)}}
        ]
        if query_or:
            query_and.append({'$or': query_or})
        if 'city' in data:
            query_and.append({'city': {'$in': data['city']}})
        else:
            data['city'] = await self.get_user_city(user_id)
            query_and.append({'$or': [{'city': {'$size': 0}}, {'city': {'$in': data['city']}}]})

        cursor = self.db.contest.aggregate(
            [
                {'$match': {'$and': query_and}},
                {'$sample': {'size': count if count else self.max_contest_count}}
            ]
        )
        contest = list()
        while await cursor.fetch_next:
            contest.append(cursor.next_object())
        return contest

    async def search_contest_random(self, user_id, data, count=None):
        user_city = await self.get_user_city(user_id)
        current_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        cursor = self.db.contest.aggregate(
            [
                {
                    '$match':
                        {
                            '$and':
                                [
                                    {'date': {'$gte': current_date}},
                                    {'date': {'$lt': current_date + datetime.timedelta(days=self.max_contest_days)}},
                                    {
                                        '$or': [
                                            {'city': {'$size': 0}},
                                            {'city': {'$in': user_city}}
                                        ]
                                    }
                                ]
                        }
                },
                {'$sample': {'size': count if count else self.max_contest_count}}
            ]
        )
        contest = list()
        while await cursor.fetch_next:
            contest.append(cursor.next_object())
        return contest

    async def search_contest_category(self, user_id, data, count=None):
        user_city = await self.get_user_city(user_id)
        if data:
            user_category = data['category']
        else:
            user_category = await self.get_user_category(user_id)
        current_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        cursor = self.db.contest.aggregate(
            [
                {
                    '$match':
                        {
                            '$and':
                                [
                                    {'date': {'$gte': current_date}},
                                    {'date': {'$lt': current_date + datetime.timedelta(days=self.max_contest_days)}},
                                    {'category': {'$in': user_category}},
                                    {
                                        '$or': [
                                            {'city': {'$size': 0}},
                                            {'city': {'$in': user_city}}
                                        ]
                                    }
                                ]
                        }
                },
                {'$sample': {'size': count if count else self.max_contest_count}}
            ]
        )
        contest = list()
        while await cursor.fetch_next:
            contest.append(cursor.next_object())
        return contest

    async def search_contest_gift(self, user_id, data, count=None):
        user_city = await self.get_user_city(user_id)
        if data:
            user_gift = data['gift']
        else:
            user_gift = await self.get_user_gift(user_id)
        user_gift = list(map(lambda item: self.normalizer.text_normalize(item), user_gift))
        random.shuffle(user_gift)
        current_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        text_search = '"%s"' % user_gift[0] if len(user_gift) == 1 else ' '.join(user_gift)
        cursor = self.db.contest.aggregate(
            [
                {
                    '$match':
                        {
                            '$and':
                                [
                                    {'date': {'$gte': current_date}},
                                    {'date': {'$lt': current_date + datetime.timedelta(days=self.max_contest_days)}},
                                    {
                                        '$text':
                                            {
                                                '$search': text_search,
                                                '$language': 'ru'
                                            }
                                    },
                                    {
                                        '$or': [
                                            {'city': {'$size': 0}},
                                            {'city': {'$in': user_city}}
                                        ]
                                    }
                                ]
                        }
                },
                {'$sample': {'size': count if count else self.max_contest_count}}
            ]
        )
        contest = list()
        while await cursor.fetch_next:
            contest.append(cursor.next_object())
        return contest
