# -*- coding: utf-8 -*-
"""Tests of dcmweb hepler functions
"""
import unittest
import time
import concurrent.futures
from dcmweb import dcmweb

class DcmwebTests(unittest.TestCase):
    """class is needed to handle object variable"""

    def __init__(self, *args, **kwargs):
        super(DcmwebTests, self).__init__(*args, **kwargs)
        self.global_sum = 0

    def test_execute_futures(self):
        """all generated futures should be executed"""
        self.global_sum = 0
        dcmweb.execute_futures(generate_futures(self.sum_future, 10), True)
        assert self.global_sum == 45

    def sum_future(self, number):
        """adds number to global variable"""
        self.global_sum += number
        return self.global_sum

def test_wait_for_futures_limit():
    """method should wait until specified limit of set"""
    running_futures = set([])
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range(5):
            running_futures.add(executor.submit(sleep_future, i))
        running_futures = dcmweb.wait_for_futures_limit(
            running_futures, 2)
        assert len(running_futures) == 2

def generate_futures(function, number_of_futures):
    """generates futures for test"""
    for i in range(number_of_futures):
        yield (function, i)

def sleep_future(seconds):
    """sleeps for specified amount of seconds"""
    time.sleep(seconds)
    return "done"
