import unittest

from stage2.recipe_bridge import select_columns
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments,digest


class RecipeBridgeTests(unittest.TestCase):
    def test_nested_complete_components_without_solver_input(self):
        p=tiny_problem()
        # Names make the two connected operations two independently chosen groups.
        p['operations'][0]['id']='P/a/step0'
        p['operations'][1]['id']='P/b/step0'
        p['operations'][1]['predecessors']=['P/a/step0']
        da=assignments(p,p['operations'][0]);db=assignments(p,p['operations'][1])
        find=lambda rows,start:next(r for r in rows if r['start']==start)
        parents=[[find(da,0),find(db,2)],[find(da,0),find(db,4)],[find(da,2),find(db,4)]]
        before=digest(parents)
        small=select_columns(p,parents,2);large=select_columns(p,parents,3)
        self.assertEqual(digest(parents),before)
        for name in small:
            self.assertTrue({digest(c)for c in small[name]}<={digest(c)for c in large[name]})
        covered={r['operation']for options in large.values()for r in options[0]}
        self.assertEqual(covered,{op['id']for op in p['operations']})
        reordered=[parents[1],parents[2],parents[0]]
        incumbent_pool=select_columns(p,reordered,2,'first_and_incumbent')
        best=parents[0]
        for row in best:
            self.assertIn([row],incumbent_pool['/'.join(row['operation'].split('/')[:2])])

    def test_invalid_or_insufficient_parents_rejected(self):
        with self.assertRaises(ValueError):select_columns(tiny_problem(),[],2)


if __name__=='__main__':unittest.main()
