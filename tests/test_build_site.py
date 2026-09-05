import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_site import build, version


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.site=self.root/'site';self.site.mkdir()
        self.book=self.root/'book';self.book.mkdir()
        (self.site/'index.html').write_text("const BASE='__BOOK_BASE__'; const RELEASE='__SITE_RELEASE__'; const CHAPTERS_ZH=[{file:'chapter.md'}];")
        (self.site/'example.html').write_text('existing report')
        (self.book/'chapter.md').write_text('# New chapter')
        (self.book/'cover.png').write_bytes(b'cover')
        subprocess.run(['git','init','-q',str(self.book)],check=True)
        subprocess.run(['git','-C',str(self.book),'add','.'],check=True)

    @patch('build_site.revision')
    def test_packages_matching_content_and_preserves_public_files(self, revision):
        revision.side_effect=lambda path: 'a'*40 if path==self.site else 'b'*40
        output=self.root/'dist';refs=build(self.site,self.book,output)
        self.assertEqual(json.loads((output/'version.json').read_text()),refs)
        self.assertEqual((output/'content'/('b'*40)/'chapter.md').read_text(),'# New chapter')
        self.assertIn('./content/'+('b'*40)+'/',(output/'index.html').read_text())
        self.assertNotIn('__SITE_RELEASE__',(output/'index.html').read_text())
        self.assertEqual((output/'example.html').read_text(),'existing report')
        self.assertEqual((output/'cover.png').read_bytes(),b'cover')
        self.assertFalse((output/'content'/('b'*40)/'.git').exists())

    @patch('build_site.revision',return_value='a'*40)
    def test_missing_chapter_aborts_before_creating_release(self,revision):
        (self.book/'chapter.md').unlink()
        output=self.root/'dist'
        with self.assertRaisesRegex(ValueError,'Missing chapter'):build(self.site,self.book,output)
        self.assertFalse(output.exists())

    @patch('build_site.revision')
    def test_either_repository_changes_release_identity(self,revision):
        revision.side_effect=['a','b','a','c','d','b']
        releases=[version(self.site,self.book)['release'] for _ in range(3)]
        self.assertEqual(len(set(releases)),3)

if __name__=='__main__':unittest.main()
