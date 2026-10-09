import contextlib
import io
import unittest
from unittest.mock import patch
from lab3.app import build_query, recommend, parse_choice, ROLES, main, parse_profile, fixed_dialog

class AppTests(unittest.TestCase):
    def ids(self, *args):
        return sorted(r['id'] for r in recommend(*args)[1])
    def test_beginner_damage(self):
        self.assertEqual(self.ids('damage','ranged','beginner','any'), ['ranger'])
    def test_support(self):
        self.assertEqual(self.ids('support','ranged','any','any'), ['bard','druid'])
    def test_armor(self):
        self.assertEqual(self.ids('damage','ranged','any','armored'), ['druid','mage','necromancer'])
    def test_undead(self):
        self.assertEqual(self.ids('support','any','beginner','undead'), ['cleric'])
    def test_no_match(self):
        self.assertEqual(self.ids('tank','ranged','beginner','any'), [])
    def test_normalization(self):
        self.assertEqual(parse_choice('  УРОН  ',ROLES),'damage')
    def test_full_match(self):
        with self.assertRaises(ValueError): parse_choice('мне нужен урон',ROLES)
    def test_injection(self):
        for bad in ['damage(X),halt', '', 'Damage', 'any']:
            with self.assertRaises(ValueError): build_query(bad,'any','any','any')
    def test_invalid_other_fields(self):
        for args in [('damage','oops','any','any'),('damage','any','oops','any'),('damage','any','any','oops')]:
            with self.assertRaises(ValueError): build_query(*args)
    def test_dialog_retry_and_delayed_output(self):
        out=io.StringIO()
        answers=iter(['ошибка','урон','дальняя','новичок','любой'])
        def answer(prompt):
            self.assertNotIn('Найдено персонажей',out.getvalue())
            return next(answers)
        with patch('builtins.input',side_effect=answer), contextlib.redirect_stdout(out):
            self.assertEqual(main(),0)
        self.assertIn('Не удалось распознать',out.getvalue())
        self.assertIn('Следопыт',out.getvalue())
    def test_fixed_profile(self):
        self.assertEqual(parse_profile(' РОЛЬ = УРОН ; дистанция=дальняя '),
                         {'роль':'damage','дистанция':'ranged'})
    def test_fixed_invalid_profiles(self):
        for value in ['', 'роль=урон', 'роль=урон;роль=защита;дистанция=любая',
                      'жанр=rpg;дистанция=любая', 'роль=маг;дистанция=дальняя',
                      'роль=урон;дистанция=дальняя;', 'роль=урон=защита;дистанция=любая']:
            with self.subTest(value=value), self.assertRaises(ValueError): parse_profile(value)
    def test_fixed_two_clarifications(self):
        with patch('builtins.input',side_effect=['роль=урон;дистанция=дальняя','новичок','любой']) as inp, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fixed_dialog(),('damage','ranged','beginner','any'))
            self.assertEqual(inp.call_count,3)
    def test_fixed_one_clarification(self):
        with patch('builtins.input',side_effect=['роль=урон;дистанция=дальняя;опыт=новичок','любой']) as inp, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fixed_dialog(),('damage','ranged','beginner','any'))
            self.assertEqual(inp.call_count,2)
    def test_fixed_full_confirmation(self):
        with patch('builtins.input',side_effect=['роль=урон;дистанция=дальняя;опыт=новичок;противник=любой','да']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fixed_dialog(),('damage','ranged','beginner','any'))
    def test_fixed_retry_end_to_end(self):
        out=io.StringIO()
        with patch('builtins.input',side_effect=['ошибка','роль=урон;дистанция=дальняя','новичок','любой']), contextlib.redirect_stdout(out):
            self.assertEqual(main(fixed=True),0)
        self.assertIn('Следопыт',out.getvalue())

    def test_exit(self):
        with patch('builtins.input',return_value='выход'),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(),0)
    def test_missing_runtime(self):
        with patch('lab3.app.shutil.which',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'swipl'): recommend('damage','any','any','any')

if __name__=='__main__': unittest.main()
