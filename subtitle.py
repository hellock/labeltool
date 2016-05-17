class Subtitle(object):

    def __init__(self, filename):
        self.filename = filename
        self.subs = {}
        self.load(filename)

    def cvt_time(self, time_text):
        [hh, mm, tmp] = time_text.split(':')
        [ss, ms] = tmp.split('.')
        [hh, mm, ss, ms] = list(map(float, [hh, mm, ss, ms]))
        return hh * 3600 + mm * 60 + ss + ms / 1000

    def load(self, filename):
        with open(filename, 'r') as fin:
            slices = fin.read().split('\n\n\n')
        for slice in slices:
            data = slice.split('\n')
            idx = data[0]
            time_slot = data[1].split(' --> ')
            start = time_slot[0]
            end = time_slot[1]
            text = '\n'.join(data[2:])
            self.subs[idx] = {'from': start, 'to': end, 'text': text}

    def get_subtitle(self, time):
        for idx in range(1, len(self.subs) + 1):
            idx = str(idx)
            if time > self.cvt_time(self.subs[idx]['to']):
                continue
            elif time >= self.cvt_time(self.subs[idx]['from']):
                return self.subs[idx]['text']
            else:
                return None

    # def draw_subtitle(self, ori_img, time):
    #     text = self.get_subtitle(time)
    #     if text is None:
    #         return ori_img
    #     else:
    #         img = ori_img.copy()
    #         font = cv2.FONT_HERSHEY_SIMPLEX
    #         cv2.putText(img, text, (10, 500), font, 4, (255, 255, 255), 2, cv2.LINE_AA)
