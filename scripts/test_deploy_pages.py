import unittest
from deploy_pages import ApiError, publish

ENV = {
    'PAGES_ARTIFACT_ID':'12345', 'GITHUB_REPOSITORY':'owner/portfolio',
    'GITHUB_TOKEN':'test-repository-token', 'GITHUB_SHA':'abc123',
    'ACTIONS_ID_TOKEN_REQUEST_URL':'https://identity.example/token',
    'ACTIONS_ID_TOKEN_REQUEST_TOKEN':'test-runtime-token',
}
ENDPOINT = 'https://api.github.com/repos/owner/portfolio/pages/deployments'


class FakeClock:
    def __init__(self): self.now = 0
    def time(self): return self.now
    def sleep(self, seconds): self.now += seconds


class DeploymentTests(unittest.TestCase):
    def run_publish(self, responses, *, timeout=600, env=ENV):
        calls = []
        clock = FakeClock()
        def request(url, token, payload=None):
            calls.append((url,token,payload))
            response = responses.pop(0)
            if isinstance(response, Exception): raise response
            return response
        result = publish(env, request=request, sleep=clock.sleep,
                         clock=clock.time, timeout=timeout)
        return result,calls,clock.now

    def test_exact_uploaded_id_without_artifact_listing(self):
        result,calls,_ = self.run_publish([
            {'value':'test-identity'},
            {'id':17,'page_url':'https://owner.github.io/'},
            {'status':'queued'},{'status':'succeed'},
        ])
        self.assertEqual(result,'https://owner.github.io/')
        self.assertEqual(calls[1],(ENDPOINT,'test-repository-token',{
            'artifact_id':12345,'pages_build_version':'abc123','oidc_token':'test-identity'}))
        self.assertTrue(all('/artifacts' not in url for url,_,_ in calls))

    def test_waits_for_new_artifact_and_temporary_status_errors(self):
        result,calls,elapsed = self.run_publish([
            {'value':'test-identity'},ApiError(404),{'id':17,'page_url':'https://owner.github.io/'},
            ApiError(503),{'status':'succeed'},
        ])
        self.assertEqual(elapsed,10)
        self.assertEqual(calls[1],calls[2])

    def test_failed_publication_remains_a_real_failure(self):
        calls = []
        responses = [{'value':'test-identity'},{'id':17}, {'status':'deployment_content_failed'},{}]
        def request(url,token,payload=None):
            calls.append(url)
            return responses.pop(0)
        with self.assertRaisesRegex(RuntimeError,'deployment_content_failed'):
            publish(ENV,request=request,sleep=lambda _:None,clock=lambda:0)
        self.assertEqual(calls[-1],ENDPOINT+'/17/cancel')

    def test_timeout_cancels_deployment(self):
        clock = FakeClock()
        calls = []
        def request(url,token,payload=None):
            calls.append(url)
            if url==ENV['ACTIONS_ID_TOKEN_REQUEST_URL']:return {'value':'test-identity'}
            if url==ENDPOINT:return {'id':17}
            return {'status':'queued'}
        with self.assertRaises(TimeoutError):
            publish(ENV,request=request,sleep=clock.sleep,clock=clock.time,timeout=10)
        self.assertEqual(calls[-1],ENDPOINT+'/17/cancel')

    def test_permission_errors_are_not_hidden_or_retried(self):
        with self.assertRaises(ApiError):
            self.run_publish([{'value':'test-identity'},ApiError(403)])

    def test_invalid_artifact_id_fails_before_any_request(self):
        with self.assertRaises(ValueError):
            self.run_publish([],env={**ENV,'PAGES_ARTIFACT_ID':''})


if __name__ == '__main__': unittest.main()
