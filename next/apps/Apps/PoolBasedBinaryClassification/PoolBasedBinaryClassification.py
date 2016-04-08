import json
import next.utils as utils
import next.apps.SimpleTargetManager

class PoolBasedBinaryClassification(object):
    def __init__(self):
        self.app_id = 'PoolBasedBinaryClassification'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()

    def initExp(self, exp_uid, exp_data, butler):
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_uid, exp_data['args']['targets']['targetset'])
        exp_data['args']['n'] = n
        del exp_data['args']['targets']

        alg_data = {}
        algorithm_keys = ['n','failure_probability']
        for key in algorithm_keys:
            if key in exp_data['args']:
                alg_data[key]=exp_data['args'][key]

        return exp_data,alg_data

    def getQuery(self, exp_uid, experiment_dict, query_request, alg_response, butler):
        target  = self.TargetManager.get_target_item(exp_uid, alg_response)
        del target['meta']
        return {'target_indices':target}

    def processAnswer(self, exp_uid, query, answer, butler):
        target = query['target_indices']

        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])
        
        # # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        # experiment = butler.experiment.get()
        # n = experiment['args']['n']
        # if num_reported_answers % ((n+4)/4) == 0:
        #     butler.job('getModel', json.dumps({'exp_uid':exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        

        algs_args_dict = {'target_index':target['target_id'],'target_label':target_label}
        query_update = {'target_index':target['target_id'],'target_label':target_label}
        return query_update,algs_args_dict

    def getModel(self, exp_uid, alg_response, args_dict, butler):
        return {'weights':alg_response[0], 'num_reported_answers':alg_response[1]}

    def getStats(self, exp_uid, stats_request, dashboard, butler):
        stat_id = stats_request['args']['stat_id']
        task = stats_request['args']['params'].get('task', None)
        alg_label = stats_request['args']['params'].get('alg_label', None)

        # These are the functions corresponding to stat_id
        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                     'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                     'compute_duration_detailed_stacked_area_plot':dashboard.compute_duration_detailed_stacked_area_plot,
                     'response_time_histogram':dashboard.response_time_histogram,
                     'network_delay_histogram':dashboard.network_delay_histogram,
                     'most_current_embedding':dashboard.most_current_embedding,
                     'test_error_multiline_plot':dashboard.test_error_multiline_plot}
        
        default = [self.app_id, exp_uid]
        args = {'api_activity_histogram':default + [task],
                'compute_duration_multiline_plot':default + [task],
                'compute_duration_detailed_stacked_area_plot':default + [task, alg_label],
                'response_time_histogram':default + [alg_label],
                'network_delay_histogram':default + [alg_label],
                'most_current_embedding':default + [alg_label],
                'test_error_multiline_plot':default}
        
        return functions[stat_id](*args[stat_id])


