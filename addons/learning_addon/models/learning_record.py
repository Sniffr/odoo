from odoo import models, fields, api


class LearningRecord(models.Model):
    _name = 'learning.record'
    _description = 'Learning Record'
    _order = 'create_date desc'

    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('odoo', 'Odoo Development'),
        ('other', 'Other')
    ], string='Category', default='odoo')
    difficulty = fields.Selection([
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], string='Difficulty Level', default='beginner')
    is_completed = fields.Boolean(string='Completed', default=False)
    completion_date = fields.Date(string='Completion Date')
    notes = fields.Html(string='Notes')

    @api.onchange('is_completed')
    def _onchange_is_completed(self):
        if self.is_completed and not self.completion_date:
            self.completion_date = fields.Date.today()
        elif not self.is_completed:
            self.completion_date = False
