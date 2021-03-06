import tensorflow as tf

from model.hyperparameter import OPTIMIZER_DIS_HP, OPTIMIZER_GEN_HP
from other.config import BATCH_SIZE
from other.nn_func import optimize_loss


class DiscriminatorOptimizer:
    def __init__(self, stack_to_train, name):
        '''

        :param models:
        :param stack_to_train: a dict consist of g, dis_real, ...
        :param name:
        '''
        with tf.name_scope(name) as scope:
            self.stack_to_train = stack_to_train
            self.variables_to_train = self._get_variables()
            self.loss = self._get_loss()
            self.optmzr = self._get_optimizer(name)
            self._summary_dis()

            # self.merge = tf.summary.merge(tf.get_collection(tf.GraphKeys.SUMMARIES, scope=scope))
            self.summaries = tf.get_collection(tf.GraphKeys.SUMMARIES, scope=scope)

    def _get_loss(self):
        lambda_ = OPTIMIZER_DIS_HP['lambda']
        dis_real = self.stack_to_train['dis_real']
        dis_wrong = self.stack_to_train['dis_wrong']
        dis_penalty = self.stack_to_train['dis_penalty']

        # w distance
        neg_w_dis = dis_wrong.score - dis_real.score
        tf.summary.scalar('w_dis', -tf.reduce_mean(neg_w_dis))

        [gradients_img, gradients_emb] = tf.gradients(dis_penalty.score,
                                                      [dis_penalty.image_input, dis_penalty.emb_input],
                                                      name='grad_img_emb')
        norm_img_square = tf.reduce_sum(tf.square(gradients_img),[1,2,3])
        norm_emb_square = tf.reduce_sum(tf.square(gradients_emb),[1])
        norm2 = tf.sqrt(norm_img_square + norm_emb_square)
        norm2_img = tf.sqrt(norm_img_square)
        norm2_emb = tf.sqrt(norm_emb_square)

        tf.summary.histogram('gradients_img', gradients_img)
        tf.summary.histogram('gradients_emb', gradients_emb)

        tf.summary.scalar('norm2', tf.reduce_mean(norm2))
        tf.summary.scalar('norm2_img', tf.reduce_mean(norm2_img))
        tf.summary.scalar('norm2_emb', tf.reduce_mean(norm2_emb))

        gp = tf.reduce_mean(tf.square(norm2 - 1))

        loss = tf.reduce_mean(dis_wrong.score) - tf.reduce_mean(dis_real.score) \
               + lambda_ * gp

        return loss

    def _get_optimizer(self, name):
        learning_rate = OPTIMIZER_DIS_HP['learning_rate']
        optimizer = OPTIMIZER_DIS_HP['optimizer']
        step = tf.Variable(0, trainable=False, name=name + '/global_step')
        optmzr = optimize_loss(self.loss, step, learning_rate, optimizer,
                               variables=self.variables_to_train)
        ret = optmzr

        return ret

    def _get_variables(self):
        model = self.stack_to_train['dis_real']
        return model.trainable_variables

    def _summary_dis(self, ):
        dis_real = self.stack_to_train['dis_real']
        # dis_fake = self.stack_to_train['dis_fake']
        real_pic = self.one_hot_inverse(dis_real.image_input) if dis_real.variable_scope_name.find(
            'seg') != -1 else dis_real.image_input
        # fake_pic = self.one_hot_inverse(dis_fake.image_input) if dis_fake.variable_scope_name.find(
        #     'seg') != -1 else dis_fake.image_input
        # concat = tf.concat([real_pic, fake_pic], axis=2)
        tf.summary.image('real_fake', real_pic, max_outputs=BATCH_SIZE)
        tf.summary.histogram('real_image', real_pic)
        # tf.summary.histogram('fake_image', fake_pic)

    def one_hot_inverse(self, pic):
        return \
            tf.cast(
                tf.expand_dims(
                    tf.arg_max(pic, -1),
                    axis=3),
                tf.float32)


class GeneratorOptimizer:
    def __init__(self, stack_to_train, name):
        with tf.name_scope(name) as scope:
            self.stack_to_train = stack_to_train
            self.variables_to_train = self._get_variables()
            self.loss = self._get_loss()
            self.optmzr = self._get_optimizer(name)

            # self.merge = tf.summary.merge(tf.get_collection(tf.GraphKeys.SUMMARIES, scope=scope))
            self.summaries = tf.get_collection(tf.GraphKeys.SUMMARIES, scope=scope)

    def _get_loss(self):
        dis_fake = self.stack_to_train['dis_fake']
        loss_dis = -tf.reduce_mean(dis_fake.score)
        # tf.summary.scalar('loss_dis', loss_dis)
        loss = loss_dis

        return loss

    def _get_optimizer(self, name):
        learning_rate = OPTIMIZER_GEN_HP['learning_rate']
        optimizer = OPTIMIZER_GEN_HP['optimizer']
        step = tf.Variable(0, trainable=False, name=name + '/global_step')
        optmzr = optimize_loss(self.loss, step, learning_rate, optimizer,
                               variables=self.variables_to_train)
        return optmzr

    def _get_variables(self):
        model = self.stack_to_train['gen']
        return model.trainable_variables
