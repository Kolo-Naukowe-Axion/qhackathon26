"""Evidence-copy integrity tests; no factory executions."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from stage2.package_final import copy_supplements
from stage2.verify_package import indexed_path


class SupplementEvidenceTests(unittest.TestCase):
    def test_replay_paths_must_be_manifest_indexed_and_inside_package(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'trace').write_text('data')
            self.assertEqual(indexed_path(root,'trace',{'trace':'digest'}),(root/'trace').resolve())
            with self.assertRaisesRegex(ValueError,'Unindexed'):indexed_path(root,'trace',{})
            with self.assertRaisesRegex(ValueError,'escaping'):indexed_path(root,'../outside',{'../outside':'digest'})
    def test_scoped_copy_records_literal_bytes_and_excludes_unlisted_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'audit';source.mkdir();(source/'proof.json').write_bytes(b'{"lower":1}\n')
            (root/'unlisted-secret').write_text('not part of evidence')
            index=root/'index.json';index.write_text(json.dumps({'offline-proof':dict(path=str(source),scope='Posthoc proof, excluded from final estimates')}))
            out=root/'package';out.mkdir();e=copy_supplements(index,out)
            p=out/e[0]['files'][0]['path']
            self.assertEqual(p.read_bytes(),b'{"lower":1}\n')
            self.assertEqual(e[0]['files'][0]['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(len(list(out.rglob('unlisted-secret'))),0)
            self.assertEqual(json.loads((out/'audit-supplement-index.json').read_text()),e)

    def test_unsafe_labels_and_internal_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'audit';source.mkdir();(source/'a').write_text('proof')
            index=root/'index.json';out=root/'package';out.mkdir()
            index.write_text(json.dumps({'../escape':dict(path=str(source),scope='audit')}))
            with self.assertRaisesRegex(ValueError,'safe path'):copy_supplements(index,out)
            (source/'link').symlink_to(root/'outside')
            (root/'outside').write_text('outside')
            index.write_text(json.dumps({'proof':dict(path=str(source),scope='audit')}))
            with self.assertRaisesRegex(ValueError,'escape'):copy_supplements(index,out)


if __name__=='__main__':unittest.main()
