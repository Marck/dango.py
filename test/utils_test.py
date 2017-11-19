import unittest

from dango import utils
import discord


class TestTypeInheritanceMap(unittest.TestCase):

    def test_lookup(self):
        m = utils.TypeMap()

        m.put(discord.abc.User, "something")
        m.put(discord.TextChannel, "something else")
        m.put(discord.Guild, "another thing")

        self.assertEquals("something", m.lookup(discord.abc.User))
        self.assertEquals("something", m.lookup(discord.User))
        self.assertEquals("something", m.lookup(discord.Member))
        self.assertEquals("something else", m.lookup(discord.TextChannel))
        self.assertEquals(None, m.lookup(discord.DMChannel))

    def test_constructed(self):
        m = utils.TypeMap({
            discord.abc.User: "something",
            discord.TextChannel: "something else",
            discord.Guild: "another thing"
        })

        self.assertEquals("something", m.lookup(discord.abc.User))
        self.assertEquals("something", m.lookup(discord.User))
        self.assertEquals("something", m.lookup(discord.Member))
        self.assertEquals("something else", m.lookup(discord.TextChannel))
        self.assertEquals(None, m.lookup(discord.DMChannel))


class TestFormattingUtils(unittest.TestCase):

    def test_clean_formatting(self):
        samples = [
            ["**`2`**", r'\*\*\`2\`\*\*'],
            ["__init__", r'\_\_init\_\_'],
            ["```Macdja38", r"\`\`\`Macdja38"]
        ]

        for sample in samples:
            self.assertEquals(sample[1], utils.clean_formatting(sample[0]))

    def test_clean_mentions(self):
        samples = [
            ["@everyone", '@\u200beveryone'],
            ["<@109379894718234624>", '<@\u200b109379894718234624>']
        ]

        for sample in samples:
            self.assertEquals(sample[1], utils.clean_mentions(sample[0]))

    def test_clean_single_backtick(self):
        samples = [
            [
                '\u200b``` test triple at beginning and end```\u200b',
                '``` test triple at beginning and end```'
            ],
            ['test ```triple``` on interior', 'test ```triple``` on interior'],
            ['` test backtick on the beginning', '` test backtick on the beginning'],
            [
                '`test backtick on the beginning no space',
                '`test backtick on the beginning no space'
            ],
            ['test double `` back ticks ``\u200b', 'test double `` back ticks ``'],
            [
                '\u200b`` test two backticks on the beginning',
                '`` test two backticks on the beginning'
            ],
            ['`\u200b', '`'],
            ['\u200b``\u200b', '``'],
            ['\u200b`` ``\u200b', '`` ``'],
            [' ``` ``\u200b', ' ``` ``']
        ]

        for sample in samples:
            self.assertEquals(sample[0], utils.clean_single_backtick(sample[1]))

    def test_uncleanable_single_backtick(self):
        with self.assertRaises(ValueError):
            utils.clean_single_backtick('test `single backtick` on interior')

    def test_clean_triple_backtick(self):
        samples = [
            # Boundaries
            ['``\u200b`\u200b', '```'],
            # In the middle of text
            [' ``\u200b` ', ' ``` '],
            # Left boundaries needs nothing
            ['``\u200b` ', '``` '],
            # even single ticks at the end
            ['the command is `command`\u200b', 'the command is `command`'],
            [' ``\u200b``\u200b`` ', ' `````` '],
            [' ``\u200b``\u200b``\u200b` ', ' ``````` '],
        ]

        for sample in samples:
            self.assertEquals(sample[0], utils.clean_triple_backtick(sample[1]))

    def test_clean_newline(self):
        samples = [
            ["\`\`\` test triple", "``` test triple"],
            ["``` test triple with `", "``` test triple with `"],
            ["Test `backtick` with extra \`", "Test `backtick` with extra `"],
            ['\`test command', '`test command'],
            ['backtick at end\`', 'backtick at end`'],
            ['double backtick \`\`', 'double backtick ``']
        ]

        for sample in samples:
            self.assertEquals(sample[0], utils.clean_newline(sample[1]))


if __name__ == "__main__":
    unittest.main()
